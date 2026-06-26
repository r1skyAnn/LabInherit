"""Category-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: int | None = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=128)
    parent_id: int | None = None
    sort_order: int | None = None


class CategoryOut(BaseModel):
    id: int
    parent_id: int | None
    name: str
    slug: str
    path: str
    sort_order: int
    created_by: int
    creator_display_name: str | None = None
    created_at: datetime
    updated_at: datetime
    children: list[CategoryOut] = []

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    items: list[CategoryOut]
    total: int
