"""File-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class FileOut(BaseModel):
    id: int
    owner_id: int
    project_id: int | None
    original_name: str
    mime_type: str
    size: int
    category: str
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NoteAttachmentOut(BaseModel):
    id: int
    note_id: int
    file_id: int
    role: str
    position: int
    created_at: datetime
    file: FileOut

    model_config = {"from_attributes": True}


class AttachmentCreate(BaseModel):
    """Attach an already-uploaded file to a note."""
    file_id: int
    role: str = Field(default="attachment", pattern="^(inline|attachment)$")
    position: int = 0


class AttachmentUpdate(BaseModel):
    role: str | None = Field(default=None, pattern="^(inline|attachment)$")
    position: int | None = None