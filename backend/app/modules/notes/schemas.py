"""Note-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    project_id: int
    category_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = None
    category_id: int | None = None
    is_pinned: bool | None = None


class NoteOut(BaseModel):
    id: int
    project_id: int
    category_id: int | None
    author_id: int
    title: str
    content: str
    author_display_name: str
    author_email: str
    author_enrollment_year: int | None
    author_graduation_year: int | None
    is_pinned: bool
    like_count: int
    comment_count: int
    liked: bool = False
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    project_title: str | None = None

    model_config = {"from_attributes": True}


class NoteListResponse(BaseModel):
    items: list[NoteOut]
    total: int
