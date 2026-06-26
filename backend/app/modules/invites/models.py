"""Invites ORM models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class Invite(Base, TimestampMixin):
    __tablename__ = "invites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    max_uses: Mapped[int] = mapped_column(BigInteger, default=1, nullable=False)
    used_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    creator: Mapped["User"] = relationship("User", back_populates="created_invites")

    __table_args__ = (
        CheckConstraint("max_uses > 0", name="invites_max_uses_positive"),
        CheckConstraint("used_count >= 0", name="invites_used_count_nonneg"),
        CheckConstraint("used_count <= max_uses", name="invites_used_le_max"),
        Index("ix_invites_active", "code", "revoked_at"),
    )

    def is_active(self, now: datetime | None = None) -> bool:
        if self.revoked_at is not None:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expires_at is not None:
            check = now or datetime.now(tz=self.expires_at.tzinfo)
            if check >= self.expires_at:
                return False
        return True
