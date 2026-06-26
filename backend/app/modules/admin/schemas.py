"""Admin dashboard schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class UserKPIs(BaseModel):
    active: int = 0
    graduated: int = 0
    archived: int = 0


class DashboardKPIs(BaseModel):
    users: UserKPIs
    pending_audits: int = 0
    open_asks: int = 0
    stale_projects: int = 0
    failed_emails: int = 0
    notes_total: int = 0
    comments_total: int = 0


class StaleProjectOut(BaseModel):
    id: int
    title: str
    status: str
    last_activity_at: datetime | None = None
    creator_display_name: str = ""

    model_config = {"from_attributes": True}


class HotNoteOut(BaseModel):
    id: int
    title: str
    project_id: int
    project_title: str = ""
    like_count: int = 0
    comment_count: int = 0

    model_config = {"from_attributes": True}


class UnansweredAskOut(BaseModel):
    id: int
    note_id: int
    project_id: int = 0
    note_title: str = ""
    asker_name: str = ""
    content: str = ""
    created_at: datetime
    days_open: int = 0

    model_config = {"from_attributes": True}


class FailedEmailOut(BaseModel):
    id: int
    to_email: str
    subject: str
    retry_count: int = 0
    last_error: str | None = None

    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    kpis: DashboardKPIs
    stale_projects: list[StaleProjectOut]
    hot_notes: list[HotNoteOut]
    unanswered_asks: list[UnansweredAskOut]
    failed_emails: list[FailedEmailOut]
