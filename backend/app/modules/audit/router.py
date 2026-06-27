"""Audit-queue HTTP routes (owner only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_owner
from app.db.session import get_db
from app.modules.audit import service
from app.modules.audit.schemas import AuditEntryOut, AuditListResponse, DecisionRequest
from app.modules.users.models import User

router = APIRouter(prefix="/admin/audit-queue", tags=["admin", "audit"])


@router.get("", response_model=AuditListResponse, summary="列出审核队列")
async def list_queue(
    user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AuditListResponse:
    items, total = await service.list_queue(
        db, user, status=status, page=page, page_size=page_size
    )
    return AuditListResponse(items=items, total=total)


@router.post("/{entry_id}/decision", response_model=AuditEntryOut, summary="审核决策")
async def decide(
    entry_id: int,
    payload: DecisionRequest,
    user: Annotated[User, Depends(require_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuditEntryOut:
    entry = await service.decide(
        db, entry_id, user, action=payload.action, note=payload.note
    )
    return entry
