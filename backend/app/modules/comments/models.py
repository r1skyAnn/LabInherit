"""Comment ORM model — plain comments + issue-style ask tracking."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class CommentStatus:
    OPEN = "open"
    ANSWERED = "answered"
    CLOSED = "closed"


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    target_type: Mapped[str] = mapped_column(String(16), nullable=False)  # "note" | "comment"
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_ask: Mapped[bool] = mapped_column(default=False, server_default="0")
    status: Mapped[str] = mapped_column(String(16), default=CommentStatus.OPEN, server_default="open")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )

    author: Mapped["User"] = relationship("User")

    @property
    def author_name(self) -> str:
        return self.author.display_name if self.author else ""

    @property
    def author_email(self) -> str:
        return self.author.email if self.author else ""

    parent: Mapped["Comment | None"] = relationship("Comment", remote_side="Comment.id", backref="replies")

    __table_args__ = (
        Index("ix_comments_target", "target_type", "target_id", "status"),
    )
