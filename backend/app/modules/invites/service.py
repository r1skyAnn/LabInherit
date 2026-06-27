"""Invite business logic: generation, validation, redemption."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.audit.models import AuditQueue, AuditStatus
from app.modules.invites.models import Invite
from app.modules.users.models import User, UserProfile, UserRole, UserStatus
from app.core.security import hash_password


def _generate_code() -> str:
    raw = secrets.token_urlsafe(9)
    return raw.upper().replace("-", "").replace("_", "")[:12]


async def create_invite(
    db: AsyncSession,
    created_by: User,
    max_uses: int = 1,
    expires_at: datetime | None = None,
    note: str | None = None,
) -> Invite:
    if not created_by.is_owner():
        raise PermissionDeniedError("只有管理员可以生成邀请码")
    code = _generate_code()
    invite = Invite(
        code=code,
        created_by=created_by.id,
        max_uses=max_uses,
        expires_at=expires_at,
        note=note,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


async def list_invites(
    db: AsyncSession,
    _: User,  # owner only, enforced by router
    include_revoked: bool = False,
) -> list[Invite]:
    stmt = select(Invite).order_by(Invite.created_at.desc())
    if not include_revoked:
        stmt = stmt.where(Invite.revoked_at.is_(None))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def revoke_invite(
    db: AsyncSession,
    invite_id: int,
    user: User,
) -> Invite:
    if not user.is_owner():
        raise PermissionDeniedError("只有管理员可以作废邀请码")
    result = await db.execute(select(Invite).where(Invite.id == invite_id))
    invite = result.scalar_one_or_none()
    if invite is None:
        raise NotFoundError("邀请码不存在")
    if invite.revoked_at is not None:
        raise ConflictError("邀请码已经作废")
    invite.revoked_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(invite)
    return invite


async def redeem_invite(
    db: AsyncSession,
    code: str,
    email: str,
    password: str,
    display_name: str,
    enrollment_year: int | None = None,
    research_direction: str | None = None,
    gender: str | None = None,
) -> User:
    # Find the invite
    result = await db.execute(
        select(Invite).where(Invite.code == code.upper())
    )
    invite = result.scalar_one_or_none()
    if invite is None:
        raise NotFoundError("邀请码无效")
    now = datetime.now(tz=timezone.utc)
    if not invite.is_active(now):
        raise ConflictError("邀请码已过期或已达使用上限")

    # Check email uniqueness
    email_result = await db.execute(select(User).where(User.email == email.lower()))
    if email_result.scalar_one_or_none() is not None:
        raise ConflictError("该邮箱已被注册")

    # Create user
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        display_name=display_name,
        status=UserStatus.ACTIVE.value,
        role=UserRole.MEMBER.value,
    )
    db.add(user)
    await db.flush()

    # Create profile
    profile = UserProfile(
        user_id=user.id,
        enrollment_year=enrollment_year,
        research_direction=research_direction,
        gender=gender,
    )
    db.add(profile)

    # Create audit record
    audit = AuditQueue(
        user_id=user.id,
        submitted_payload={
            "enrollment_year": enrollment_year,
            "research_direction": research_direction,
            "gender": gender,
        },
        status=AuditStatus.PENDING.value,
    )
    db.add(audit)

    # Atomically increment used_count
    await db.execute(
        update(Invite)
        .where(Invite.id == invite.id)
        .values(used_count=Invite.used_count + 1)
    )

    await db.commit()
    return user


async def register_without_invite(
    db: AsyncSession,
    email: str,
    password: str,
    display_name: str,
    enrollment_year: int | None = None,
    research_direction: str | None = None,
    gender: str | None = None,
) -> User:
    email_result = await db.execute(select(User).where(User.email == email.lower()))
    if email_result.scalar_one_or_none() is not None:
        raise ConflictError("该邮箱已被注册")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        display_name=display_name,
        status=UserStatus.ACTIVE.value,
        role=UserRole.MEMBER.value,
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(
        user_id=user.id,
        enrollment_year=enrollment_year,
        research_direction=research_direction,
        gender=gender,
    )
    db.add(profile)

    audit = AuditQueue(
        user_id=user.id,
        submitted_payload={
            "enrollment_year": enrollment_year,
            "research_direction": research_direction,
            "gender": gender,
        },
        status=AuditStatus.PENDING.value,
    )
    db.add(audit)

    await db.commit()
    return user
