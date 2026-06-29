"""File & NoteAttachment ORM models — unified attachment system.

A `File` is one physical upload (image/document/video/other) owned by a user.
A `NoteAttachment` links a File to a Note in one of two roles:
  - inline: image embedded in markdown body
  - attachment: a downloadable file at the bottom of the note
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models import User
    from app.modules.notes.models import Note


# Allowed categories — derived from mime type at upload time
FILE_CATEGORIES = ("image", "document", "video", "audio", "archive", "mindmap", "other")

# Map extensions to category for nice grouping in UI
EXT_CATEGORY_MAP: dict[str, str] = {
    # images
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image",
    "webp": "image", "svg": "image", "bmp": "image", "ico": "image",
    # documents
    "pdf": "document", "doc": "document", "docx": "document",
    "xls": "document", "xlsx": "document", "ppt": "document", "pptx": "document",
    "txt": "document", "md": "document", "rtf": "document",
    # videos
    "mp4": "video", "webm": "video", "mov": "video", "avi": "video", "mkv": "video",
    # audio
    "mp3": "audio", "wav": "audio", "ogg": "audio", "m4a": "audio",
    # archives
    "zip": "archive", "rar": "archive", "7z": "archive", "tar": "archive", "gz": "archive",
    # mindmaps
    "mm": "mindmap", "km": "mindmap", "xmind": "mindmap",
}


class File(Base, TimestampMixin):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    owner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Optional project scoping (notes belong to projects)
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Original metadata
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Stored filename on disk: {uuid}.{ext}
    stored_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # Subdirectory relative to UPLOAD_DIR (e.g. "2026-06")
    subdir: Mapped[str] = mapped_column(String(32), nullable=False, default="")

    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False, default="other")

    # Soft-delete flag — preserves file history but hides from queries
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    owner: Mapped["User"] = relationship("User")
    note_attachments: Mapped[list["NoteAttachment"]] = relationship(
        "NoteAttachment", back_populates="file", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_files_owner_category", "owner_id", "category"),
        Index("ix_files_subdir_stored", "subdir", "stored_name"),
    )

    @property
    def url(self) -> str:
        """Public URL path (served via /uploads/* static mount).

        Path on disk is `<UPLOAD_DIR>/files/<subdir>/<stored_name>`,
        so the URL must include the `files/` segment.
        """
        parts = ["files"]
        if self.subdir:
            parts.append(self.subdir)
        parts.append(self.stored_name)
        return f"/uploads/{'/'.join(parts)}"


class NoteAttachment(Base):
    __tablename__ = "note_attachments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    note_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # role: 'inline' (image embedded in markdown) | 'attachment' (downloadable file)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="attachment")
    # Display order within the note
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    note: Mapped["Note"] = relationship("Note")
    file: Mapped["File"] = relationship("File", back_populates="note_attachments")

    __table_args__ = (
        Index("ix_note_attachments_note", "note_id"),
    )