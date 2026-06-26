"""Global search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.notes import service as notes_service
from app.modules.notes.schemas import NoteListResponse, NoteOut

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=NoteListResponse, summary="全站搜索笔记")
async def global_search(
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
) -> NoteListResponse:
    notes, total = await notes_service.list_notes(db, q=q, page=page, page_size=page_size)
    items = []
    for note in notes:
        items.append(NoteOut(
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
            created_at=note.created_at,
            updated_at=note.updated_at,
            category_name=note.category.name if note.category else None,
            project_title=note.project.title if note.project else None,
        ))
    return NoteListResponse(items=items, total=total)
