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
    # Notify the applicant by email
    from app.core.email import send_email
    if entry.user_email:
        action_text = "通过" if payload.action == "approve" else "未通过"
        await send_email(
            to=entry.user_email,
            subject=f"[LabInherit] 你的注册申请已被{action_text}",
            body_text=(
                f"你好，{entry.user_display_name}：\n\n"
                f"你的 LabInherit 注册申请已被管理员{action_text}。\n"
                + (f"审核备注：{payload.note}\n\n" if payload.note else "\n")
                + ("你现在可以登录平台了。\n" if payload.action == "approve" else "如有疑问请联系实验室管理员。\n")
            ),
        )
    return entry
