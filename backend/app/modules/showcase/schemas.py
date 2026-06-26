"""Showcase-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ShowcaseCreate(BaseModel):
    type: str = Field(..., pattern="^(achievement|blessing)$")
    title: str = Field(default="", max_length=200)
    description: str | None = None
    image_url: str | None = None
    pdf_url: str | None = None
    contact_info: str | None = Field(None, max_length=256)
    experience: str | None = None


class ShowcaseUpdate(BaseModel):
    title: str | None = Field(None, max_length=200)
    description: str | None = None
    image_url: str | None = None
    pdf_url: str | None = None
    contact_info: str | None = Field(None, max_length=256)
    experience: str | None = None


class ShowcaseOut(BaseModel):
    id: int
    author_id: int
    type: str
    title: str
    description: str | None = None
    image_url: str | None = None
    pdf_url: str | None = None
    contact_info: str | None = None
    experience: str | None = None
    created_at: datetime
    updated_at: datetime
    author_name: str = ""
    author_email: str = ""
    author_enrollment_year: int | None = None
    author_graduation_year: int | None = None

    model_config = {"from_attributes": True}


class ShowcaseListResponse(BaseModel):
    items: list[ShowcaseOut]
    total: int
