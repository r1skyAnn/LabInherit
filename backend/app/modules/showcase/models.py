"""ShowcaseItem ORM model — achievements + blessings wall."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class ShowcaseItem(Base):
    __tablename__ = "showcase_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # "achievement" | "blessing"
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    contact_info: Mapped[str | None] = mapped_column(String(256), nullable=True)
    experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
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

    @property
    def author_enrollment_year(self) -> int | None:
        profile = self.author.profile if self.author else None
        return profile.enrollment_year if profile else None

    @property
    def author_graduation_year(self) -> int | None:
        profile = self.author.profile if self.author else None
        return profile.graduation_year if profile else None

    __table_args__ = (Index("ix_showcase_type", "type"),)
