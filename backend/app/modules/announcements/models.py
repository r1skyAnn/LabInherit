"""Announcement ORM models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User


class Announcement(Base, TimestampMixin):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_pinned: Mapped[bool] = mapped_column(default=False, nullable=False)

    author: Mapped["User"] = relationship("User")

    @property
    def author_display_name(self) -> str | None:
        return self.author.display_name if self.author else None

    __table_args__ = (
        Index("ix_announcements_author_id", "author_id"),
    )
