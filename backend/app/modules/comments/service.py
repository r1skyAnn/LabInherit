"""Comment business logic — CRUD, status machine, and side effects."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.modules.comments.models import Comment, CommentStatus


async def _incr_note_comment_count(db: AsyncSession, note_id: int, delta: int) -> None:
    from app.modules.notes.models import Note
    result = await db.execute(select(Note).where(Note.id == note_id))
    note = result.scalar_one_or_none()
    if note is not None:
        note.comment_count = max(0, note.comment_count + delta)


async def create_comment(
    db: AsyncSession,
    author_id: int,
    target_type: str,
    target_id: int,
    data: dict,
) -> Comment:
    comment = Comment(
        target_type=target_type,
        target_id=target_id,
        parent_id=data.get("parent_id"),
        author_id=author_id,
        content=data["content"],
        is_ask=data.get("is_ask", False),
        status=data.get("status", CommentStatus.OPEN),
    )
    db.add(comment)

    if target_type == "note":
        await _incr_note_comment_count(db, target_id, 1)

    await db.commit()
    await db.refresh(comment, attribute_names=["author"])
    return comment


async def list_comments(
    db: AsyncSession,
    target_type: str,
    target_id: int,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Comment], int]:
    base = (
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.target_type == target_type, Comment.target_id == target_id)
        .order_by(Comment.created_at.asc())
    )

    count_q = select(func.count()).select_from(
        select(Comment).where(Comment.target_type == target_type, Comment.target_id == target_id).subquery()
    )
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    return list(result.scalars().all()), total


async def get_comment(db: AsyncSession, comment_id: int) -> Comment:
    result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.author))
        .where(Comment.id == comment_id)
    )
    comment = result.scalar_one_or_none()
    if comment is None:
        raise NotFoundError("评论不存在")
    return comment


async def update_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> Comment:
    comment = await get_comment(db, comment_id)
    if comment.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有评论作者可以修改")

    if "content" in data and data["content"] is not None:
        comment.content = data["content"]

    if "status" in data and data["status"] is not None:
        _validate_transition(comment.status, data["status"])
        comment.status = data["status"]

    if "is_ask" in data and data["is_ask"] is not None:
        comment.is_ask = data["is_ask"]

    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(
    db: AsyncSession,
    comment_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    comment = await get_comment(db, comment_id)
    if comment.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有评论作者可以删除")

    target_type = comment.target_type
    target_id = comment.target_id

    await db.delete(comment)

    if target_type == "note":
        await _incr_note_comment_count(db, target_id, -1)

    await db.commit()


async def get_note_comment_count(db: AsyncSession, note_id: int) -> int:
    result = await db.execute(
        select(func.count()).where(
            Comment.target_type == "note",
            Comment.target_id == note_id,
        )
    )
    return result.scalar_one() or 0


async def list_asks_for_project(
    db: AsyncSession,
    project_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Comment], int]:
    """List all open asks for a project — cross-note aggregation."""
    from app.modules.notes.models import Note

    base = (
        select(Comment)
        .options(selectinload(Comment.author))
        .join(Note, Note.id == Comment.target_id)
        .where(
            Comment.target_type == "note",
            Note.project_id == project_id,
            Comment.status == CommentStatus.OPEN,
        )
        .order_by(Comment.created_at.desc())
    )

    count_q = (
        select(func.count())
        .select_from(Comment)
        .join(Note, Note.id == Comment.target_id)
        .where(
            Comment.target_type == "note",
            Note.project_id == project_id,
            Comment.status == CommentStatus.OPEN,
        )
    )
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    return list(result.scalars().all()), total


def _validate_transition(old: str, new: str) -> None:
    valid = {
        CommentStatus.OPEN: {CommentStatus.ANSWERED, CommentStatus.CLOSED},
        CommentStatus.ANSWERED: {CommentStatus.CLOSED},
        CommentStatus.CLOSED: set(),
    }
    allowed = valid.get(old, set())
    if new not in allowed:
        raise PermissionDeniedError(f"不能从 {old} 转为 {new}")
