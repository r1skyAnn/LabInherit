"""Cross-cutting FastAPI dependencies: auth, role checks, owner-or-admin checks."""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
)
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.users.models import User

# tokenUrl is the OpenAPI client identifier; actual login is POST /api/v1/auth/login
# with JSON body — the scheme is only used for the Authorize button in Swagger.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.APP_BASE_URL}/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if not token:
        raise UnauthorizedError("缺少认证令牌")
    try:
        payload = decode_access_token(token)
    except JWTError as exc:
        raise UnauthorizedError(f"无效令牌: {exc}") from exc

    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError("令牌格式错误")
    try:
        user_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("令牌格式错误") from exc

    result = await db.execute(
        select(User)
        .options(selectinload(User.profile))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError("用户不存在或已被删除")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str) -> Callable[..., Any]:
    """Factory: dependency that 403s if current user doesn't have any of `roles`."""
    allowed = set(roles)

    async def _checker(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise PermissionDeniedError(
                f"需要角色之一: {', '.join(sorted(allowed))}"
            )
        return user

    return _checker


async def require_admin_or_owner(user: CurrentUser) -> User:
    if user.role not in ("admin", "owner"):
        raise PermissionDeniedError("需要管理员或所有者权限")
    return user


def require_owner_or_admin_resource(
    model: type, id_param: str = "id"
) -> Callable[..., Any]:
    """Factory: load `model` by `id_param`; 403 unless user is owner-of-record or admin+.

    Usage:
        @router.delete("/notes/{id}", dependencies=[Depends(require_owner_or_admin_resource(Note))])
    """

    async def _checker(
        request: Request,
        user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> Any:
        resource_id = request.path_params.get(id_param)
        if resource_id is None:
            raise NotFoundError("资源不存在")
        try:
            rid = int(resource_id)
        except ValueError as exc:
            raise NotFoundError("资源不存在") from exc

        result = await db.execute(select(model).where(model.id == rid))  # type: ignore[attr-defined]
        obj = result.scalar_one_or_none()
        if obj is None:
            raise NotFoundError("资源不存在")

        owner_attr = getattr(obj, "author_id", None) or getattr(obj, "user_id", None)
        if owner_attr is not None and owner_attr == user.id:
            return obj
        if user.is_admin_or_above():
            return obj
        raise PermissionDeniedError("无权限操作此资源")

    return _checker
