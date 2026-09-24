"""Showcase HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.showcase import service
from app.modules.showcase.schemas import (
    ShowcaseCreate,
    ShowcaseListResponse,
    ShowcaseOut,
    ShowcaseUpdate,
)

router = APIRouter(prefix="/showcase", tags=["showcase"])


@router.get("", response_model=ShowcaseListResponse, summary="获取展示墙列表")
async def list_showcase(
    db: Annotated[AsyncSession, Depends(get_db)],
    type: str | None = Query(None, pattern="^(achievement|blessing)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
) -> ShowcaseListResponse:
    items, total = await service.list_items(db, type=type, page=page, page_size=page_size)
    return ShowcaseListResponse(items=[ShowcaseOut.model_validate(i) for i in items], total=total)


@router.post("", response_model=ShowcaseOut, summary="添加展示墙条目")
async def create_showcase(
    payload: ShowcaseCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShowcaseOut:
    item = await service.create_item(db, user, payload.model_dump(exclude_unset=True))
    return ShowcaseOut.model_validate(item)


@router.get("/{item_id}", response_model=ShowcaseOut, summary="获取展示条目详情")
async def get_showcase(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShowcaseOut:
    item = await service.get_item(db, item_id)
    return ShowcaseOut.model_validate(item)


@router.patch("/{item_id}", response_model=ShowcaseOut, summary="更新条目")
async def update_showcase(
    item_id: int,
    payload: ShowcaseUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShowcaseOut:
    item = await service.update_item(
        db, item_id, user.id, user.is_owner(),
        payload.model_dump(exclude_unset=True),
    )
    return ShowcaseOut.model_validate(item)


@router.delete("/{item_id}", summary="删除条目")
async def delete_showcase(
    item_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_item(db, item_id, user.id, user.is_owner())
    return {"detail": "已删除"}
