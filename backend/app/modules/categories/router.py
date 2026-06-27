"""Category HTTP routes — global tree."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_active_member
from app.db.session import get_db
from app.modules.categories import service
from app.modules.categories.schemas import (
    CategoryCreate,
    CategoryListResponse,
    CategoryOut,
    CategoryUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/categories", tags=["categories"])


def _cat_to_out(cat) -> CategoryOut:
    return CategoryOut(
        id=cat.id,
        parent_id=cat.parent_id,
        name=cat.name,
        slug=cat.slug,
        path=cat.path,
        sort_order=cat.sort_order,
        created_by=cat.created_by,
        creator_display_name=cat.creator.display_name if cat.creator else None,
        created_at=cat.created_at,
        updated_at=cat.updated_at,
        children=[],
    )


def _tree_to_outs(nodes: list[dict]) -> list[CategoryOut]:
    result: list[CategoryOut] = []
    for node in nodes:
        item = CategoryOut(
            id=node["id"],
            parent_id=node["parent_id"],
            name=node["name"],
            slug=node["slug"],
            path=node["path"],
            sort_order=node["sort_order"],
            created_by=node["created_by"],
            creator_display_name=node["creator_display_name"],
            created_at=node["created_at"],
            updated_at=node["updated_at"],
            children=_tree_to_outs(node["children"]),
        )
        result.append(item)
    return result


@router.post("", response_model=CategoryOut, summary="创建分类")
async def create_category(
    _: Annotated[User, Depends(require_active_member)],
    payload: CategoryCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryOut:
    cat = await service.create_category(db, created_by=user.id, data=payload.model_dump(exclude_unset=True))
    return _cat_to_out(cat)


@router.get("", response_model=CategoryListResponse, summary="获取全局分类树")
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryListResponse:
    categories = await service.list_categories(db)
    tree = service.build_tree(categories)
    return CategoryListResponse(items=_tree_to_outs(tree), total=len(categories))


@router.get("/{category_id}", response_model=CategoryOut, summary="获取分类详情")
async def get_category(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryOut:
    cat = await service.get_category(db, category_id)
    return _cat_to_out(cat)


@router.patch("/{category_id}", response_model=CategoryOut, summary="更新分类")
async def update_category(
    _: Annotated[User, Depends(require_active_member)],
    category_id: int,
    payload: CategoryUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryOut:
    cat = await service.update_category(
        db, category_id, user.id, user.is_owner(),
        payload.model_dump(exclude_unset=True),
    )
    return _cat_to_out(cat)


@router.delete("/{category_id}", summary="删除分类")
async def delete_category(
    _: Annotated[User, Depends(require_active_member)],
    category_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_category(db, category_id, user.id, user.is_owner())
    return {"detail": "分类已删除"}
