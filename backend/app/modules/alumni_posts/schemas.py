"""Alumni post-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AlumniPostCreate(BaseModel):
    type: str = Field(min_length=1, max_length=16)  # referral | tech | resource
    title: str = Field(min_length=1, max_length=200)
    content: str | None = None
    company: str | None = Field(None, max_length=128)
    position: str | None = Field(None, max_length=128)
    contact_info: str | None = Field(None, max_length=256)
    tags: str | None = Field(None, max_length=256)


class AlumniPostUpdate(BaseModel):
    type: str | None = Field(None, max_length=16)
    title: str | None = Field(None, min_length=1, max_length=200)
    content: str | None = None
    company: str | None = Field(None, max_length=128)
    position: str | None = Field(None, max_length=128)
    contact_info: str | None = Field(None, max_length=256)
    tags: str | None = Field(None, max_length=256)


class AlumniPostOut(BaseModel):
    id: int
    author_id: int
    author_display_name: str | None = None
    type: str
    title: str
    content: str | None = None
    company: str | None = None
    position: str | None = None
    contact_info: str | None = None
    tags: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlumniPostListResponse(BaseModel):
    items: list[AlumniPostOut]
    total: int
