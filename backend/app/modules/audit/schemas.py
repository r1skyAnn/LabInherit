"""Audit-queue Pydantic schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditEntryOut(BaseModel):
    id: int
    user_id: int
    user_email: str
    user_display_name: str
    submitted_payload: dict
    reviewer_id: int | None
    reviewer_email: str | None
    status: str
    decision_note: str | None
    decided_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DecisionRequest(BaseModel):
    action: str = "approve"  # "approve" | "reject"
    note: str | None = None


class AuditListResponse(BaseModel):
    items: list[AuditEntryOut]
    total: int
