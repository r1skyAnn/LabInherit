"""Category business logic — global materialized path tree."""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.categories.models import Category


def _slugify(name: str) -> str:
    raw = name.lower().strip()
    raw = re.sub(r"[^a-z0-9一-鿿\s-]", "", raw)
    return re.sub(r"[\s-]+", "-", raw)


async def create_category(
    db: AsyncSession,
    created_by: int,
    data: dict,
) -> Category:
    slug = _slugify(data["name"])
    parent_id = data.get("parent_id")

    existing = await db.execute(
        select(Category).where(
            Category.parent_id == parent_id,
            Category.slug == slug,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("同级下已存在同名分类")

    category = Category(
        parent_id=parent_id,
        name=data["name"],
        slug=slug,
        path="",
        sort_order=data.get("sort_order", 0),
        created_by=created_by,
    )
    db.add(category)
    await db.flush()

    if parent_id is not None:
        parent_result = await db.execute(
            select(Category.path).where(Category.id == parent_id)
        )
        parent_path = parent_result.scalar_one_or_none()
        if parent_path is None:
            raise NotFoundError("父分类不存在")
        category.path = f"{parent_path}/{category.id}"
    else:
        category.path = str(category.id)

    await db.commit()
    await db.refresh(category, attribute_names=["creator"])
    return category


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.creator))
        .order_by(Category.path, Category.sort_order, Category.name)
    )
    return list(result.scalars().all())


def build_tree(categories: list[Category]) -> list[dict]:
    lookup: dict[int, dict] = {}
    roots: list[dict] = []

    for cat in categories:
        node = {
            "id": cat.id,
            "parent_id": cat.parent_id,
            "name": cat.name,
            "slug": cat.slug,
            "path": cat.path,
            "sort_order": cat.sort_order,
            "created_by": cat.created_by,
            "creator_display_name": cat.creator.display_name if cat.creator else None,
            "created_at": cat.created_at,
            "updated_at": cat.updated_at,
            "children": [],
        }
        lookup[cat.id] = node

    for cat in categories:
        node = lookup[cat.id]
        if cat.parent_id is not None and cat.parent_id in lookup:
            lookup[cat.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return roots


async def get_category(db: AsyncSession, category_id: int) -> Category:
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.creator))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise NotFoundError("分类不存在")
    return category


async def update_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> Category:
    category = await get_category(db, category_id)
    if category.created_by != user_id and not is_owner:
        raise PermissionDeniedError("只有分类创建者可以修改")

    old_path = category.path

    if "name" in data and data["name"] is not None:
        new_slug = _slugify(data["name"])
        existing = await db.execute(
            select(Category).where(
                Category.parent_id == category.parent_id,
                Category.slug == new_slug,
                Category.id != category_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("同级下已存在同名分类")
        category.slug = new_slug
        category.name = data["name"]

    if "parent_id" in data and data["parent_id"] != category.parent_id:
        new_parent_id = data["parent_id"]
        if new_parent_id == category_id:
            raise ConflictError("不能将分类设置为自己的子分类")
        if new_parent_id is not None:
            parent_result = await db.execute(
                select(Category.path).where(Category.id == new_parent_id)
            )
            parent_path = parent_result.scalar_one_or_none()
            if parent_path is None:
                raise NotFoundError("目标父分类不存在")
            if parent_path.startswith(old_path + "/") or parent_path == old_path:
                raise ConflictError("不能将分类移动到自己的子分类下")
            category.path = f"{parent_path}/{category.id}"
            category.parent_id = new_parent_id
        else:
            category.path = str(category.id)
            category.parent_id = None

    if "sort_order" in data and data["sort_order"] is not None:
        category.sort_order = data["sort_order"]

    await db.commit()

    new_path = category.path
    if old_path != new_path:
        descendants = await db.execute(
            select(Category).where(
                Category.path.startswith(old_path + "/"),
            )
        )
        for desc in descendants.scalars().all():
            desc.path = new_path + desc.path[len(old_path):]
        await db.commit()

    await db.refresh(category)
    return category


async def delete_category(
    db: AsyncSession,
    category_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    category = await get_category(db, category_id)
    if category.created_by != user_id and not is_owner:
        raise PermissionDeniedError("只有分类创建者可以删除")
    await db.delete(category)
    await db.commit()
