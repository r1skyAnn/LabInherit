"""Project-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str | None = None
    category_id: int | None = None
    priority: str = Field(default="medium")
    tech_stack: str | None = Field(default=None, max_length=512)
    repo_url: str | None = Field(default=None, max_length=512)
    demo_url: str | None = Field(default=None, max_length=512)
    zip_url: str | None = Field(default=None, max_length=512)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    is_public: bool = Field(default=True)
    allowed_viewer_ids: list[int] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    category_id: int | None = None
    status: str | None = None
    priority: str | None = None
    tech_stack: str | None = Field(None, max_length=512)
    repo_url: str | None = Field(None, max_length=512)
    demo_url: str | None = Field(None, max_length=512)
    zip_url: str | None = Field(None, max_length=512)
    started_at: datetime | None = None
    ended_at: datetime | None = None
    is_public: bool | None = None
    allowed_viewer_ids: list[int] | None = None


class ProjectOut(BaseModel):
    id: int
    title: str
    description: str | None
    category_id: int | None = None
    category_name: str | None = None
    status: str
    priority: str
    tech_stack: str | None
    repo_url: str | None
    demo_url: str | None
    zip_url: str | None = None
    started_at: datetime | None
    ended_at: datetime | None
    created_by: int
    creator_display_name: str | None = None
    is_public: bool
    allowed_viewer_ids: list[int] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    items: list[ProjectOut]
    total: int
