"""Notification HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.notifications import service
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationOut,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationListResponse, summary="获取通知列表")
async def list_notifications(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NotificationListResponse:
    items, total, unread_count = await service.list_notifications(
        db, user.id, unread_only=unread_only, page=page, page_size=page_size,
    )
    return NotificationListResponse(
        items=[NotificationOut.model_validate(n) for n in items],
        total=total,
        unread_count=unread_count,
    )


@router.get("/unread-count", summary="获取未读通知数")
async def get_unread_count(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    count = await service.get_unread_count(db, user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read", summary="标记已读")
async def mark_read(
    notification_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.mark_read(db, notification_id, user.id)
    return {"detail": "ok"}


@router.post("/read-all", summary="全部已读")
async def read_all(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    count = await service.mark_all_read(db, user.id)
    return {"detail": f"已标记 {count} 条通知为已读"}
