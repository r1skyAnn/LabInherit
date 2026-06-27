"""Note business logic — CRUD, filtering, and like."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.notes.models import Note, NoteLike
from app.modules.users.models import User


async def create_note(
    db: AsyncSession,
    author: User,
    data: dict,
) -> Note:
    note = Note(
        project_id=data["project_id"],
        category_id=data.get("category_id"),
        author_id=author.id,
        title=data["title"],
        content=data.get("content", ""),
        author_display_name=author.display_name,
        author_email=author.email,
        author_enrollment_year=author.profile.enrollment_year if author.profile else None,
        author_graduation_year=author.profile.graduation_year if author.profile else None,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note, attribute_names=["author", "project", "category"])
    return note


async def list_notes(
    db: AsyncSession,
    project_id: int | None = None,
    category_id: int | None = None,
    author_id: int | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Note], int]:
    base = (
        select(Note)
        .options(
            selectinload(Note.author),
            selectinload(Note.project),
            selectinload(Note.category),
        )
        .order_by(Note.is_pinned.desc(), Note.created_at.desc())
    )
    if project_id is not None:
        base = base.where(Note.project_id == project_id)
    if category_id is not None:
        base = base.where(Note.category_id == category_id)
    if author_id is not None:
        base = base.where(Note.author_id == author_id)
    if q:
        base = base.where(
            Note.title.contains(q) | Note.content.contains(q)
        )

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    notes = list(result.scalars().all())
    return notes, total


async def get_note(db: AsyncSession, note_id: int) -> Note:
    result = await db.execute(
        select(Note)
        .options(
            selectinload(Note.author),
            selectinload(Note.project),
            selectinload(Note.category),
        )
        .where(Note.id == note_id)
    )
    note = result.scalar_one_or_none()
    if note is None:
        raise NotFoundError("笔记不存在")
    return note


async def update_note(
    db: AsyncSession,
    note_id: int,
    user_id: int,
    is_owner: bool,
    data: dict,
) -> Note:
    note = await get_note(db, note_id)
    if note.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有笔记作者可以修改")

    for key in ("title", "content", "is_pinned"):
        if key in data and data[key] is not None:
            setattr(note, key, data[key])
    if "category_id" in data:
        note.category_id = data["category_id"]

    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(
    db: AsyncSession,
    note_id: int,
    user_id: int,
    is_owner: bool,
) -> None:
    note = await get_note(db, note_id)
    if note.author_id != user_id and not is_owner:
        raise PermissionDeniedError("只有笔记作者可以删除")
    await db.delete(note)
    await db.commit()


async def like_note(db: AsyncSession, note_id: int, user_id: int) -> Note:
    note = await get_note(db, note_id)
    # Check if already liked
    existing = await db.execute(
        select(NoteLike).where(NoteLike.note_id == note_id, NoteLike.user_id == user_id)
    )
    if existing.scalar_one_or_none():
        raise ConflictError("你已经点过赞了")
    db.add(NoteLike(note_id=note_id, user_id=user_id))
    note.like_count += 1
    await db.commit()
    await db.refresh(note)
    return note


async def unlike_note(db: AsyncSession, note_id: int, user_id: int) -> Note:
    note = await get_note(db, note_id)
    result = await db.execute(
        select(NoteLike).where(NoteLike.note_id == note_id, NoteLike.user_id == user_id)
    )
    like_record = result.scalar_one_or_none()
    if like_record is None:
        raise NotFoundError("你还没有点赞")
    await db.delete(like_record)
    note.like_count = max(0, note.like_count - 1)
    await db.commit()
    await db.refresh(note)
    return note


async def get_liked_note_ids(db: AsyncSession, user_id: int, note_ids: list[int]) -> set[int]:
    result = await db.execute(
        select(NoteLike.note_id).where(
            NoteLike.user_id == user_id,
            NoteLike.note_id.in_(note_ids),
        )
    )
    return {row[0] for row in result.all()}
