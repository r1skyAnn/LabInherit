"""Comment-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    parent_id: int | None = None
    is_ask: bool = False
    status: str | None = None


class CommentUpdate(BaseModel):
    content: str | None = None
    status: str | None = None
    is_ask: bool | None = None  # 普通评论 → 升级为追问


class CommentOut(BaseModel):
    id: int
    target_type: str
    target_id: int
    parent_id: int | None = None
    author_id: int
    content: str
    is_ask: bool = False
    status: str
    created_at: datetime
    updated_at: datetime
    author_name: str = ""
    author_email: str = ""

    model_config = {"from_attributes": True}


class CommentListResponse(BaseModel):
    items: list[CommentOut]
    total: int
