"""Member list schemas (read-only, no model needed — derives from users table)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MemberOut(BaseModel):
    id: int
    display_name: str
    email: str
    role: str
    status: str
    enrollment_year: int | None = None
    graduation_year: int | None = None
    research_direction: str | None = None
    current_affiliation: str | None = None
    bio: str | None = None
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberListResponse(BaseModel):
    items: list[MemberOut]
    total: int
