"""Announcement HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.announcements import service
from app.modules.announcements.schemas import (
    AnnouncementCreate,
    AnnouncementListResponse,
    AnnouncementOut,
    AnnouncementUpdate,
)

router = APIRouter(prefix="/announcements", tags=["announcements"])


def _build_out(a: "Announcement") -> AnnouncementOut:
    return AnnouncementOut(
        id=a.id,
        title=a.title,
        content=a.content,
        author_id=a.author_id,
        author_display_name=a.author.display_name if a.author else None,
        is_pinned=a.is_pinned,
        created_at=a.created_at,
        updated_at=a.updated_at,
    )


@router.post("", response_model=AnnouncementOut, summary="发布公告（成员）")
async def create_announcement(
    payload: AnnouncementCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnnouncementOut:
    ann = await service.create_announcement(
        db,
        author_id=user.id,
        data=payload.model_dump(exclude_unset=True),
    )
    return _build_out(ann)


@router.get("", response_model=AnnouncementListResponse, summary="列出公告")
async def list_announcements(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AnnouncementListResponse:
    items, total = await service.list_announcements(
        db, page=page, page_size=page_size
    )
    return AnnouncementListResponse(
        items=[_build_out(a) for a in items],
        total=total,
    )


@router.get("/{announcement_id}", response_model=AnnouncementOut, summary="获取公告详情")
async def get_announcement(
    announcement_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnnouncementOut:
    ann = await service.get_announcement(db, announcement_id)
    return _build_out(ann)


@router.patch("/{announcement_id}", response_model=AnnouncementOut, summary="更新公告")
async def update_announcement(
    announcement_id: int,
    payload: AnnouncementUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AnnouncementOut:
    ann = await service.update_announcement(
        db, announcement_id, user.id, user.is_owner(), payload.model_dump(exclude_unset=True)
    )
    return _build_out(ann)


@router.delete("/{announcement_id}", summary="删除公告")
async def delete_announcement(
    announcement_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_announcement(db, announcement_id, user.id, user.is_owner())
    return {"detail": "公告已删除"}
