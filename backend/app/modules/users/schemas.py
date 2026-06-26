"""User-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, EmailStr


class UserProfileOut(BaseModel):
    enrollment_year: int | None = None
    graduation_year: int | None = None
    research_direction: str | None = None
    current_affiliation: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    gender: str | None = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str
    status: str
    role: str
    last_login_at: datetime | None
    profile: UserProfileOut | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, min_length=1, max_length=64)
    enrollment_year: int | None = None
    graduation_year: int | None = None
    research_direction: str | None = Field(None, max_length=128)
    current_affiliation: str | None = Field(None, max_length=128)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=512)
    gender: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
