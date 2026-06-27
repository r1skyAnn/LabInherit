"""Project ORM models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.categories.models import Category


class ProjectStatus(str, Enum):
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ProjectPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProjectStatus.ACTIVE.value
    )
    priority: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ProjectPriority.MEDIUM.value
    )
    tech_stack: Mapped[str | None] = mapped_column(String(512), nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    demo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    zip_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    category: Mapped["Category | None"] = relationship("Category")
    creator: Mapped["User"] = relationship("User")
    allowed_viewers: Mapped[list["ProjectViewer"]] = relationship(
        "ProjectViewer", back_populates="project", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('planning', 'active', 'paused', 'completed', 'abandoned')",
            name="projects_status_valid",
        ),
        CheckConstraint(
            "priority IN ('low', 'medium', 'high')",
            name="projects_priority_valid",
        ),
        Index("ix_projects_status", "status"),
        Index("ix_projects_created_by", "created_by"),
    )

    def is_active(self) -> bool:
        return self.status == ProjectStatus.ACTIVE.value


class ProjectViewer(Base):
    """Users allowed to view a private project."""
    __tablename__ = "project_viewers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="allowed_viewers")

    __table_args__ = (
        Index("ix_project_viewers_unique", "project_id", "user_id", unique=True),
    )
