"""Note HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.notes import service
from app.modules.notes.schemas import (
    NoteCreate,
    NoteListResponse,
    NoteOut,
    NoteUpdate,
)

router = APIRouter(prefix="/notes", tags=["notes"])


def _build_out(note, liked: bool = False) -> NoteOut:
    return NoteOut(
        id=note.id,
        project_id=note.project_id,
        category_id=note.category_id,
        author_id=note.author_id,
        title=note.title,
        content=note.content,
        author_display_name=note.author_display_name,
        author_email=note.author_email,
        author_enrollment_year=note.author_enrollment_year,
        author_graduation_year=note.author_graduation_year,
        is_pinned=note.is_pinned,
        like_count=note.like_count,
        comment_count=note.comment_count,
        liked=liked,
        created_at=note.created_at,
        updated_at=note.updated_at,
        category_name=note.category.name if note.category else None,
        project_title=note.project.title if note.project else None,
    )


@router.post("", response_model=NoteOut, summary="创建笔记")
async def create_note(
    payload: NoteCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteOut:
    note = await service.create_note(db, user, payload.model_dump(exclude_unset=True))
    return _build_out(note)


@router.get("", response_model=NoteListResponse, summary="列出笔记")
async def list_notes(
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: int | None = Query(None),
    category_id: int | None = Query(None),
    author_id: int | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> NoteListResponse:
    notes, total = await service.list_notes(
        db, project_id=project_id, category_id=category_id,
        author_id=author_id, q=q, page=page, page_size=page_size,
    )
    return NoteListResponse(items=[_build_out(n) for n in notes], total=total)


@router.get("/{note_id}", response_model=NoteOut, summary="获取笔记详情")
async def get_note(
    note_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteOut:
    note = await service.get_note(db, note_id)
    return _build_out(note)


@router.patch("/{note_id}", response_model=NoteOut, summary="更新笔记")
async def update_note(
    note_id: int,
    payload: NoteUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteOut:
    note = await service.update_note(
        db, note_id, user.id, user.is_admin_or_above(),
        payload.model_dump(exclude_unset=True),
    )
    return _build_out(note)


@router.delete("/{note_id}", summary="删除笔记")
async def delete_note(
    note_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_note(db, note_id, user.id, user.is_admin_or_above())
    return {"detail": "笔记已删除"}


@router.post("/{note_id}/like", response_model=NoteOut, summary="点赞笔记")
async def like_note(
    note_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteOut:
    note = await service.like_note(db, note_id, user.id)
    return _build_out(note, liked=True)


@router.delete("/{note_id}/like", response_model=NoteOut, summary="取消点赞")
async def unlike_note(
    note_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteOut:
    note = await service.unlike_note(db, note_id, user.id)
    return _build_out(note)
