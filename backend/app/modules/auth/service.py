"""Auth business logic: login, password reset.

Public functions raise `AppError` subclasses; routers turn them into HTTP responses.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import BackgroundTasks
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import send_email
from app.core.exceptions import (
    PermissionDeniedError,
    UnauthorizedError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_password_reset_token,
    hash_password,
    verify_password,
)
from app.modules.audit.models import AuditStatus
from app.modules.users.models import User, UserStatus


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    """Validate credentials and return the active, approved user.

    Raises UnauthorizedError or PermissionDeniedError with a sanitized message.
    """
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        # Identical message regardless of which is wrong — don't leak user existence
        raise UnauthorizedError("邮箱或密码错误")
    if user.status != UserStatus.ACTIVE.value:
        raise PermissionDeniedError("账号已被停用或归档")
    # Registration-gate: non-owner users must have an approved audit record.
    # Owners (created by seed or DB admin) skip this check.
    from app.modules.audit.models import AuditQueue  # avoid circular at module load

    if user.role != "owner":
        approved = await db.execute(
            select(AuditQueue.id)
            .where(AuditQueue.user_id == user.id, AuditQueue.status == AuditStatus.APPROVED.value)
            .limit(1)
        )
        if approved.scalar_one_or_none() is None:
            raise PermissionDeniedError("账号尚未通过审核，请联系管理员")
    return user


def issue_token(user: User) -> tuple[str, int]:
    """Create an access token. Returns (token, expires_in_seconds)."""
    expires = settings.JWT_EXPIRE_MINUTES * 60
    token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role, "status": user.status, "email": user.email},
    )
    return token, expires


async def update_last_login(db: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(tz=timezone.utc)
    db.add(user)
    await db.commit()


async def request_password_reset(
    db: AsyncSession, email: str, background: BackgroundTasks | None = None
) -> None:
    """Look up user; if found, queue a reset email (best-effort)."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()
    if user is None:
        # No-op: never reveal whether an email is registered
        return
    token = create_password_reset_token(user.id)
    reset_link = f"{settings.APP_BASE_URL}/reset-password?token={token}"
    body = (
        f"你好，{user.display_name}：\n\n"
        f"我们收到了重置你 LabInherit 密码的请求。\n"
        f"请点击以下链接在 30 分钟内重置你的密码：\n\n"
        f"  {reset_link}\n\n"
        f"如果你没有请求重置密码，请忽略本邮件。\n"
    )

    async def _send() -> None:
        await send_email(to=user.email, subject="[LabInherit] 重置你的密码", body_text=body)

    if background is not None:
        background.add_task(_send)
    else:
        await _send()


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    if len(new_password) < 8:
        raise ValidationError("密码至少需要 8 个字符")
    try:
        payload = decode_password_reset_token(token)
    except JWTError as exc:
        raise ValidationError(f"无效或已过期的重置链接: {exc}") from exc
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise ValidationError("用户不存在")
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.commit()
