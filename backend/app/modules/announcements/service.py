"""Announcement business logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.modules.announcements.models import Announcement


async def create_announcement(
    db: AsyncSession,
    author_id: int,
    data: dict,
) -> Announcement:
    announcement = Announcement(author_id=author_id, **data)
    db.add(announcement)
    await db.commit()
    # refresh with relationship option so author is available for response serialization
    await db.refresh(announcement, attribute_names=["author"])
    return announcement


async def list_announcements(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Announcement], int]:
    base = (
        select(Announcement)
        .options(selectinload(Announcement.author))
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
    )
    count_q = select(func.count()).select_from(Announcement)
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    announcements = list(result.scalars().all())
    return announcements, total


async def get_announcement(db: AsyncSession, announcement_id: int) -> Announcement:
    result = await db.execute(
        select(Announcement)
        .options(selectinload(Announcement.author))
        .where(Announcement.id == announcement_id)
    )
    announcement = result.scalar_one_or_none()
    if announcement is None:
        raise NotFoundError("公告不存在")
    return announcement


async def update_announcement(
    db: AsyncSession,
    announcement_id: int,
    user_id: int,
    is_admin: bool,
    data: dict,
) -> Announcement:
    announcement = await get_announcement(db, announcement_id)
    if announcement.author_id != user_id and not is_admin:
        raise PermissionDeniedError("只有公告作者可以修改")
    for key, value in data.items():
        setattr(announcement, key, value)
    await db.commit()
    await db.refresh(announcement)
    return announcement


async def delete_announcement(
    db: AsyncSession,
    announcement_id: int,
    user_id: int,
    is_admin: bool,
) -> None:
    announcement = await get_announcement(db, announcement_id)
    if announcement.author_id != user_id and not is_admin:
        raise PermissionDeniedError("只有公告作者可以删除")
    await db.delete(announcement)
    await db.commit()
