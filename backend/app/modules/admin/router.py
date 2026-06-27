"""Admin dashboard + user management routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_owner
from app.db.session import get_db
from app.modules.admin import service
from app.modules.admin.schemas import DashboardResponse
from app.modules.users.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Dashboard ─────────────────────────────────────


@router.get("/dashboard", response_model=DashboardResponse, summary="管理看板")
async def get_dashboard(
    _: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    return await service.get_dashboard(db)


# ── User management ───────────────────────────────


class RoleUpdate(BaseModel):
    role: str  # member / owner


class StatusUpdate(BaseModel):
    status: str  # active / graduated / archived


@router.post("/users/{user_id}/role", summary="变更用户角色")
async def change_user_role(
    user_id: int,
    payload: RoleUpdate,
    actor: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.update_user_role(db, user_id, payload.role, actor)
    return {"detail": "ok"}


@router.post("/users/{user_id}/status", summary="变更用户状态")
async def change_user_status(
    user_id: int,
    payload: StatusUpdate,
    actor: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.update_user_status(db, user_id, payload.status, actor)
    return {"detail": "ok"}
