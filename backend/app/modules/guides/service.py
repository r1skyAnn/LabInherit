"""Guide business logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.modules.guides.models import Guide


async def create_guide(
    db: AsyncSession,
    author_id: int,
    data: dict,
) -> Guide:
    # Auto-generate slug from title if not provided
    if not data.get("slug"):
        import re
        slug = data["title"].lower().strip()
        slug = re.sub(r"[^a-z0-9一-鿿]+", "-", slug).strip("-")
        base = slug
        i = 1
        while True:
            existing = await db.execute(select(Guide).where(Guide.slug == slug))
            if not existing.scalar_one_or_none():
                break
            slug = f"{base}-{i}"
            i += 1
        data["slug"] = slug
    guide = Guide(author_id=author_id, **data)
    db.add(guide)
    await db.commit()
    await db.refresh(guide)
    return guide


async def list_guides(
    db: AsyncSession,
    tag: str | None = None,
) -> list[Guide]:
    base = (
        select(Guide)
        .options(selectinload(Guide.author))
        .order_by(Guide.is_pinned.desc(), Guide.sort_order, Guide.title)
    )
    if tag:
        base = base.where(Guide.tag == tag)
    result = await db.execute(base)
    return list(result.scalars().all())


async def get_guide(db: AsyncSession, slug: str) -> Guide:
    result = await db.execute(
        select(Guide)
        .options(selectinload(Guide.author))
        .where(Guide.slug == slug)
    )
    guide = result.scalar_one_or_none()
    if guide is None:
        raise NotFoundError("指南不存在")
    return guide


async def update_guide(
    db: AsyncSession,
    guide_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> Guide:
    guide = await db.execute(
        select(Guide).where(Guide.id == guide_id)
    )
    guide = guide.scalar_one_or_none()
    if guide is None:
        raise NotFoundError("指南不存在")
    if guide.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有编辑者可以修改")

    for key in ("title", "content", "tag", "related_projects", "sort_order", "is_pinned"):
        if key in data and data[key] is not None:
            setattr(guide, key, data[key])

    await db.commit()
    await db.refresh(guide)
    return guide


async def delete_guide(
    db: AsyncSession,
    guide_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    guide = await db.execute(select(Guide).where(Guide.id == guide_id))
    guide = guide.scalar_one_or_none()
    if guide is None:
        raise NotFoundError("指南不存在")
    if guide.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有编辑者可以删除")
    await db.delete(guide)
    await db.commit()
