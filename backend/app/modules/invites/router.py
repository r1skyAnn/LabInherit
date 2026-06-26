"""Invite HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_admin_or_owner
from app.db.session import get_db
from app.modules.invites import service
from app.modules.invites.schemas import (
    InviteCreateRequest,
    InviteOut,
    RedeemRequest,
    RedeemResponse,
    RegisterRequest,
)
from app.modules.users.models import User

router = APIRouter(prefix="/invites", tags=["invites"])


@router.post("", response_model=InviteOut, summary="创建邀请码（管理员）")
async def create_invite(
    payload: InviteCreateRequest,
    user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteOut:
    invite = await service.create_invite(
        db,
        created_by=user,
        max_uses=payload.max_uses,
        expires_at=payload.expires_at,
        note=payload.note,
    )
    return InviteOut.model_validate(invite)


@router.get("", response_model=list[InviteOut], summary="列出邀请码（管理员）")
async def list_invites(
    user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_revoked: bool = Query(False),
) -> list[InviteOut]:
    invites = await service.list_invites(db, user, include_revoked=include_revoked)
    return [InviteOut.model_validate(i) for i in invites]


@router.post("/{invite_id}/revoke", response_model=InviteOut, summary="作废邀请码（管理员）")
async def revoke_invite(
    invite_id: int,
    user: Annotated[User, Depends(require_admin_or_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteOut:
    invite = await service.revoke_invite(db, invite_id, user)
    return InviteOut.model_validate(invite)


# ── Public endpoint ────────────────────────────────────────────────

@router.post(
    "/redeem",
    response_model=RedeemResponse,
    summary="使用邀请码注册（公开）",
)
async def redeem_invite(
    payload: RedeemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedeemResponse:
    user = await service.redeem_invite(
        db,
        code=payload.code,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        enrollment_year=payload.enrollment_year,
        research_direction=payload.research_direction,
        gender=payload.gender,
    )
    return RedeemResponse(submitted_email=user.email)


@router.post(
    "/register",
    response_model=RedeemResponse,
    summary="无邀请码注册（公开，进审核队列）",
)
async def register_without_invite(
    payload: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedeemResponse:
    user = await service.register_without_invite(
        db,
        email=payload.email,
        password=payload.password,
        display_name=payload.display_name,
        enrollment_year=payload.enrollment_year,
        research_direction=payload.research_direction,
        gender=payload.gender,
    )
    return RedeemResponse(submitted_email=user.email)
