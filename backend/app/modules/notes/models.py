"""Note ORM model — Markdown notes with author snapshots."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.projects.models import Project
    from app.modules.categories.models import Category


class NoteLike(Base):
    __tablename__ = "note_likes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("note_id", "user_id", name="uq_note_likes_note_user"),
        Index("ix_note_likes_note_id", "note_id"),
    )


class Note(Base, TimestampMixin):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # Author snapshots — preserved even if the user is later archived
    author_display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    author_email: Mapped[str] = mapped_column(String(255), nullable=False)
    author_enrollment_year: Mapped[int | None] = mapped_column(nullable=True)
    author_graduation_year: Mapped[int | None] = mapped_column(nullable=True)

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    author: Mapped["User"] = relationship("User")
    project: Mapped["Project"] = relationship("Project")
    category: Mapped["Category | None"] = relationship("Category")

    __table_args__ = (
        Index("ix_notes_project_category", "project_id", "category_id"),
        Index("ix_notes_is_pinned", "is_pinned"),
    )
