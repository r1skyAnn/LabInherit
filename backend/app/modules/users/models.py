"""Users + user profiles ORM models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.audit.models import AuditQueue
    from app.modules.invites.models import Invite


class UserStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    GRADUATED = "graduated"
    ARCHIVED = "archived"


class UserRole(str, Enum):
    MEMBER = "member"
    OWNER = "owner"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default=UserStatus.ACTIVE.value)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default=UserRole.MEMBER.value)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["UserProfile | None"] = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    audit_records: Mapped[list["AuditQueue"]] = relationship(
        "AuditQueue",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="[audit_queue.c.user_id]",
    )
    created_invites: Mapped[list["Invite"]] = relationship(
        "Invite",
        back_populates="creator",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'disabled', 'graduated', 'archived')",
            name="users_status_valid",
        ),
        CheckConstraint(
            "role IN ('member', 'owner')",
            name="users_role_valid",
        ),
    )

    def is_active_member(self) -> bool:
        return self.status == UserStatus.ACTIVE.value

    def is_owner(self) -> bool:
        return self.role == UserRole.OWNER.value


class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    enrollment_year: Mapped[int | None] = mapped_column(nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(nullable=True)
    research_direction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    current_affiliation: Mapped[str | None] = mapped_column(String(128), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(8), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="profile")
