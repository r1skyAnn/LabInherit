"""Guide HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.guides import service
from app.modules.guides.schemas import (
    GuideCreate,
    GuideListResponse,
    GuideOut,
    GuideUpdate,
)

router = APIRouter(prefix="/guides", tags=["guides"])


def _can_create(user) -> bool:
    if user.role == "owner": return True
    if user.is_owner(): return True
    if user.status == "graduated": return True
    if user.profile and user.profile.enrollment_year:
        from datetime import datetime
        return datetime.utcnow().year - user.profile.enrollment_year >= 2
    return False


def _can_update(user) -> bool:
    if user.role == "owner": return True
    if user.is_owner(): return True
    if user.status == "graduated": return False
    if user.profile and user.profile.enrollment_year:
        from datetime import datetime
        return datetime.utcnow().year - user.profile.enrollment_year >= 2
    return False


def _build_out(guide) -> GuideOut:
    return GuideOut(
        id=guide.id,
        title=guide.title,
        slug=guide.slug,
        content=guide.content,
        tag=guide.tag,
        related_projects=guide.related_projects,
        sort_order=guide.sort_order,
        is_pinned=guide.is_pinned,
        author_id=guide.author_id,
        author_name=guide.author.display_name if guide.author else "",
        created_at=guide.created_at,
        updated_at=guide.updated_at,
    )


@router.get("", response_model=GuideListResponse, summary="列出指南")
async def list_guides(
    db: Annotated[AsyncSession, Depends(get_db)],
    tag: str | None = Query(None),
) -> GuideListResponse:
    items = await service.list_guides(db, tag=tag)
    return GuideListResponse(items=[_build_out(g) for g in items], total=len(items))


@router.get("/{slug}", response_model=GuideOut, summary="获取指南详情")
async def get_guide(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    guide = await service.get_guide(db, slug)
    return _build_out(guide)


@router.post("", response_model=GuideOut, summary="创建指南")
async def create_guide(
    payload: GuideCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    from app.core.exceptions import PermissionDeniedError
    if not _can_create(user):
        raise PermissionDeniedError("只有导师、师兄（入学2年以上）或已毕业成员可以创建指南")
    guide = await service.create_guide(db, author_id=user.id, data=payload.model_dump(exclude_unset=True))
    return _build_out(guide)


@router.patch("/{guide_id}", response_model=GuideOut, summary="更新指南")
async def update_guide(
    guide_id: int,
    payload: GuideUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    from app.core.exceptions import PermissionDeniedError
    if not _can_update(user):
        raise PermissionDeniedError("毕业成员只能添加不能修改，导师和师兄可以编辑")
    guide = await service.update_guide(db, guide_id, user.id, _can_update(user), payload.model_dump(exclude_unset=True))
    return _build_out(guide)


@router.delete("/{guide_id}", summary="删除指南")
async def delete_guide(
    guide_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    from app.core.exceptions import PermissionDeniedError
    if user.role != "owner":
        raise PermissionDeniedError("只有导师可以删除指南")
    await service.delete_guide(db, guide_id, user.id, True)
    return {"detail": "已删除"}
