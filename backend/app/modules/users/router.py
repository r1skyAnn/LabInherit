"""User profile HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.users import service
from app.modules.users.schemas import (
    ChangePasswordRequest,
    UserOut,
    UserUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut, summary="获取当前用户信息")
async def get_me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.patch("/me", response_model=UserOut, summary="更新个人资料")
async def update_me(
    payload: UserUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    data = payload.model_dump(exclude_unset=True)
    updated = await service.update_me(db, user, data)
    return UserOut.model_validate(updated)


@router.post("/me/change-password", summary="修改密码")
async def change_password(
    payload: ChangePasswordRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.change_password(
        db, user, payload.old_password, payload.new_password
    )
    return {"detail": "密码已修改"}
