"""Audit queue ORM models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.types import JSON as GenericJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class AuditStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AuditQueue(Base, TimestampMixin):
    __tablename__ = "audit_queue"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitted_payload: Mapped[dict] = mapped_column(
        MySQLJSON().with_variant(GenericJSON(), "sqlite"),
        nullable=False,
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AuditStatus.PENDING.value
    )
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(
        "User", back_populates="audit_records", foreign_keys=[user_id]
    )
    reviewer: Mapped["User | None"] = relationship(
        "User", foreign_keys=[reviewer_id]
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="audit_status_valid",
        ),
        Index("ix_audit_user_status", "user_id", "status"),
    )
