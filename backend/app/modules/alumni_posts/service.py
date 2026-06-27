"""Alumni post business logic."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import PermissionDeniedError, NotFoundError
from app.modules.alumni_posts.models import AlumniPost


async def create_alumni_post(
    db: AsyncSession,
    author_id: int,
    data: dict,
) -> AlumniPost:
    post = AlumniPost(author_id=author_id, **data)
    db.add(post)
    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post


async def list_alumni_posts(
    db: AsyncSession,
    post_type: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AlumniPost], int]:
    base = (
        select(AlumniPost)
        .options(selectinload(AlumniPost.author))
        .order_by(AlumniPost.created_at.desc())
    )
    if post_type:
        base = base.where(AlumniPost.type == post_type)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    posts = list(result.scalars().all())
    return posts, total


async def get_alumni_post(db: AsyncSession, post_id: int) -> AlumniPost:
    result = await db.execute(
        select(AlumniPost)
        .options(selectinload(AlumniPost.author))
        .where(AlumniPost.id == post_id)
    )
    post = result.scalar_one_or_none()
    if post is None:
        raise NotFoundError("帖子不存在")
    return post


async def update_alumni_post(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    is_admin: bool,
    data: dict,
) -> AlumniPost:
    post = await get_alumni_post(db, post_id)
    if post.author_id != user_id and not is_admin:
        raise PermissionDeniedError("只有作者可以修改此帖子")
    for key, value in data.items():
        if value is not None:
            setattr(post, key, value)
    await db.commit()
    await db.refresh(post)
    return post


async def delete_alumni_post(
    db: AsyncSession,
    post_id: int,
    user_id: int,
    is_admin: bool,
) -> None:
    post = await get_alumni_post(db, post_id)
    if post.author_id != user_id and not is_admin:
        raise PermissionDeniedError("只有作者或管理员可以删除此帖子")
    await db.delete(post)
    await db.commit()
