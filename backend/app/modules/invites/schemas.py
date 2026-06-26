"""Invite-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class InviteCreateRequest(BaseModel):
    max_uses: int = Field(default=1, ge=1, le=1000)
    expires_at: datetime | None = None
    note: str | None = Field(default=None, max_length=255)


class InviteOut(BaseModel):
    id: int
    code: str
    max_uses: int
    used_count: int
    expires_at: datetime | None
    note: str | None
    revoked_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class RedeemRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=64)
    enrollment_year: int | None = None
    research_direction: str | None = Field(default=None, max_length=128)
    gender: str | None = None


class RegisterRequest(BaseModel):
    """Registration without invite code — goes to audit queue."""
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=64)
    enrollment_year: int | None = None
    research_direction: str | None = Field(default=None, max_length=128)
    gender: str | None = None


class RedeemResponse(BaseModel):
    detail: str = "注册申请已提交，请等待管理员审核"
    submitted_email: str
