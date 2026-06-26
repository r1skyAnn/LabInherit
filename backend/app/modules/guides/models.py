"""Guide ORM model — onboarding wiki pages."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.modules.users.models import User


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tag: Mapped[str] = mapped_column(String(32), nullable=False, default="intro", server_default="intro")
    related_projects: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array like "[1,2]"
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.utcnow())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow()
    )

    author: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("slug", name="uq_guides_slug"),
        Index("ix_guides_tag", "tag"),
        Index("ix_guides_slug", "slug"),
    )
