"""Alumni Posts ORM model — graduation sharing, referrals, tech trends."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class AlumniPostType(str, Enum):
    REFERRAL = "referral"      # 内推
    TECH = "tech"              # 技术分享
    RESOURCE = "resource"     # 资源分享


class AlumniPost(Base):
    __tablename__ = "alumni_posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # referral | tech | resource
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    company: Mapped[str | None] = mapped_column(String(128), nullable=True)  # for referral
    position: Mapped[str | None] = mapped_column(String(128), nullable=True)  # for referral
    contact_info: Mapped[str | None] = mapped_column(String(256), nullable=True)  # for referral
    tags: Mapped[str | None] = mapped_column(String(256), nullable=True)  # comma-separated
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )

    author: Mapped["User"] = relationship("User")

    @property
    def author_display_name(self) -> str | None:
        return self.author.display_name if self.author else None

    __table_args__ = (
        Index("ix_alumni_posts_type", "type"),
        Index("ix_alumni_posts_created_at", "created_at"),
    )
