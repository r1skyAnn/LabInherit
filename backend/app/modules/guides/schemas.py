"""Guide-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from app.modules.files.schemas import FileOut
from pydantic import BaseModel, Field


class GuideCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    slug: str = Field(default="", max_length=200)
    content: str = ""
    tag: str = "intro"
    related_projects: str | None = None
    sort_order: int = 0
    is_pinned: bool = False


class GuideUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = None
    tag: str | None = None
    related_projects: str | None = None
    sort_order: int | None = None
    is_pinned: bool | None = None


class GuideOut(BaseModel):
    id: int
    title: str
    slug: str
    content: str
    tag: str
    related_projects: str | None = None
    sort_order: int
    is_pinned: bool
    author_id: int
    author_name: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GuideListResponse(BaseModel):
    items: list[GuideOut]
    total: int


class GuideAttachmentOut(BaseModel):
    id: int
    guide_id: int
    file_id: int
    role: str
    position: int
    created_at: datetime
    file: FileOut

    model_config = {"from_attributes": True}


# Re-use file attachment schemas from the unified files module
from app.modules.files.schemas import AttachmentCreate, AttachmentUpdate  # noqa: E402, F401
