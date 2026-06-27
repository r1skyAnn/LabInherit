"""Showcase business logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.modules.showcase.models import ShowcaseItem
from app.modules.users.models import User, UserProfile


async def create_item(
    db: AsyncSession,
    author: User,
    data: dict,
) -> ShowcaseItem:
    if data["type"] == "blessing" and not _can_bless(author):
        raise PermissionDeniedError("只有导师、师兄（入学2年以上）或已毕业成员可以留下寄语")

    # For blessings, auto-generate title from description if not provided
    if data["type"] == "blessing" and not data.get("title"):
        desc = data.get("description") or ""
        data["title"] = desc[:50] + ("..." if len(desc) > 50 else "") if desc else "寄语"

    item = ShowcaseItem(author_id=author.id, **data)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def list_items(
    db: AsyncSession,
    type: str | None = None,
    page: int = 1,
    page_size: int = 30,
) -> tuple[list[ShowcaseItem], int]:
    base = (
        select(ShowcaseItem)
        .options(selectinload(ShowcaseItem.author).joinedload(User.profile))
        .order_by(ShowcaseItem.created_at.desc())
    )
    if type:
        base = base.where(ShowcaseItem.type == type)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    return list(result.scalars().all()), total


async def get_item(db: AsyncSession, item_id: int) -> ShowcaseItem:
    result = await db.execute(
        select(ShowcaseItem)
        .options(selectinload(ShowcaseItem.author).joinedload(User.profile))
        .where(ShowcaseItem.id == item_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise NotFoundError("条目不存在")
    return item


async def update_item(
    db: AsyncSession,
    item_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> ShowcaseItem:
    item = await get_item(db, item_id)
    if item.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有作者可以修改")

    for key in ("title", "description", "image_url", "pdf_url", "contact_info", "experience"):
        if key in data and data[key] is not None:
            setattr(item, key, data[key])

    await db.commit()
    await db.refresh(item)
    return item


def _can_bless(user: User) -> bool:
    if user.role == "owner":
        return True
    if user.status == "graduated":
        return True
    profile = user.profile
    if profile and profile.enrollment_year:
        from datetime import datetime
        return datetime.utcnow().year - profile.enrollment_year >= 2
    return False


async def delete_item(
    db: AsyncSession,
    item_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    item = await get_item(db, item_id)
    if item.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有作者可以删除")
    await db.delete(item)
    await db.commit()
