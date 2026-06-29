"""Alumni post HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.alumni_posts import service
from app.modules.alumni_posts.schemas import (
    AlumniPostCreate,
    AlumniPostListResponse,
    AlumniPostOut,
    AlumniPostUpdate,
)
from app.modules.users.models import UserRole, UserStatus

router = APIRouter(prefix="/alumni-posts", tags=["alumni-posts"])


def _build_out(post: "AlumniPost") -> AlumniPostOut:
    return AlumniPostOut(
        id=post.id,
        author_id=post.author_id,
        author_display_name=post.author.display_name if post.author else None,
        type=post.type,
        title=post.title,
        content=post.content,
        company=post.company,
        position=post.position,
        contact_info=post.contact_info,
        tags=post.tags,
        created_at=post.created_at,
        updated_at=post.updated_at,
    )


@router.post("", response_model=AlumniPostOut, summary="创建毕业人员帖子")
async def create_alumni_post(
    payload: AlumniPostCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlumniPostOut:
    # 任何登录用户都可以发布（实习生也可能需要发布内推/资源信息）
    from app.core.exceptions import PermissionDeniedError
    if user.status == UserStatus.ARCHIVED.value:
        raise PermissionDeniedError("账号已归档，无法发布")
    post = await service.create_alumni_post(
        db,
        author_id=user.id,
        data=payload.model_dump(exclude_unset=True),
    )
    return _build_out(post)


@router.get("", response_model=AlumniPostListResponse, summary="列出毕业人员帖子")
async def list_alumni_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    type: str | None = Query(None, description="筛选类型: referral | tech | resource"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AlumniPostListResponse:
    posts, total = await service.list_alumni_posts(
        db, post_type=type, page=page, page_size=page_size
    )
    return AlumniPostListResponse(
        items=[_build_out(p) for p in posts],
        total=total,
    )


@router.get("/{post_id}", response_model=AlumniPostOut, summary="获取帖子详情")
async def get_alumni_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlumniPostOut:
    post = await service.get_alumni_post(db, post_id)
    return _build_out(post)


@router.patch("/{post_id}", response_model=AlumniPostOut, summary="更新帖子")
async def update_alumni_post(
    post_id: int,
    payload: AlumniPostUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlumniPostOut:
    post = await service.update_alumni_post(
        db, post_id, user.id, user.is_owner(), payload.model_dump(exclude_unset=True)
    )
    return _build_out(post)


@router.delete("/{post_id}", summary="删除帖子")
async def delete_alumni_post(
    post_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_alumni_post(db, post_id, user.id, user.is_owner())
    return {"detail": "帖子已删除"}
