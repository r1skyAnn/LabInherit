"""Auth HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.auth import service
from app.modules.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="账号密码登录")
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    user = await service.authenticate(db, payload.email, payload.password)
    token, expires = service.issue_token(user)
    await service.update_last_login(db, user)
    return TokenResponse(access_token=token, expires_in=expires)


@router.post("/logout", response_model=LogoutResponse, summary="登出（前端清 token 即可）")
async def logout(_user: CurrentUser) -> LogoutResponse:
    return LogoutResponse()


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    summary="请求重置密码（发邮件）",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ForgotPasswordResponse:
    await service.request_password_reset(db, payload.email, background)
    return ForgotPasswordResponse()


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    summary="使用 token 重置密码",
)
async def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResetPasswordResponse:
    await service.reset_password(db, payload.token, payload.new_password)
    return ResetPasswordResponse()
