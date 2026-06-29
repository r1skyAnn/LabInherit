"""File service — upload, attachment management, ownership checks."""

from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.modules.files.models import EXT_CATEGORY_MAP, FILE_CATEGORIES, File, NoteAttachment
from app.modules.notes.models import Note
from app.modules.users.models import User


# ── Upload policy ────────────────────────────────────────────
ALLOWED_MIME_PREFIXES = (
    "image/",
    "video/",
    "audio/",
    "text/",
    "application/pdf",
    "application/zip",
    "application/x-zip-compressed",
    "application/msword",
    "application/vnd.openxmlformats-officedocument",
    "application/vnd.ms-excel",
    "application/vnd.ms-powerpoint",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    "application/x-tar",
    "application/gzip",
    "application/octet-stream",  # for .mm / .km / .xmind — they have generic mime
)

MAX_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB


def _category_for(ext: str, mime: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext in EXT_CATEGORY_MAP:
        return EXT_CATEGORY_MAP[ext]
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    if mime in ("application/pdf", "application/msword",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "application/vnd.ms-powerpoint",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "text/plain", "text/markdown"):
        return "document"
    if mime in ("application/zip", "application/x-zip-compressed",
                "application/x-rar-compressed", "application/x-7z-compressed"):
        return "archive"
    return "other"


async def save_upload(
    db: AsyncSession,
    uploader: User,
    file: UploadFile,
    project_id: int | None,
) -> File:
    """Validate, persist to disk, and record metadata in the DB."""
    if not file.filename:
        raise ValidationError("缺少文件名")

    # Validate mime type
    mime = file.content_type or "application/octet-stream"
    if not any(mime.startswith(p) for p in ALLOWED_MIME_PREFIXES):
        raise ValidationError(f"不支持的文件类型: {mime}")

    contents = await file.read()
    size = len(contents)
    if size == 0:
        raise ValidationError("空文件")
    if size > MAX_SIZE_BYTES:
        raise ValidationError(f"文件过大，最大 {MAX_SIZE_BYTES // 1024 // 1024} MB")

    # Build storage path: uploads/files/YYYY-MM/{uuid}.{ext}
    now = datetime.now(timezone.utc)
    subdir = now.strftime("%Y-%m")
    original_ext = Path(file.filename).suffix.lower().lstrip(".") or "bin"
    # Sanitize extension — alphanumeric only
    safe_ext = "".join(c for c in original_ext if c.isalnum()) or "bin"
    stored_name = f"{uuid.uuid4().hex}.{safe_ext}"

    base = Path(settings.UPLOAD_DIR) / "files" / subdir
    base.mkdir(parents=True, exist_ok=True)
    target = base / stored_name

    target.write_bytes(contents)

    category = _category_for(safe_ext, mime)

    record = File(
        owner_id=uploader.id,
        project_id=project_id,
        original_name=file.filename,
        stored_name=stored_name,
        subdir=subdir,
        mime_type=mime,
        size=size,
        category=category,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


def file_to_out(f: File) -> dict:
    return {
        "id": f.id,
        "owner_id": f.owner_id,
        "project_id": f.project_id,
        "original_name": f.original_name,
        "mime_type": f.mime_type,
        "size": f.size,
        "category": f.category,
        "url": f.url,
        "created_at": f.created_at,
    }


async def get_file(db: AsyncSession, file_id: int) -> File:
    result = await db.execute(select(File).where(File.id == file_id, File.is_deleted.is_(False)))
    f = result.scalar_one_or_none()
    if f is None:
        raise NotFoundError("文件不存在")
    return f


async def delete_file(db: AsyncSession, file_id: int, user_id: int, is_owner_role: bool) -> None:
    """Soft-delete: marks is_deleted=True and removes file from disk."""
    f = await get_file(db, file_id)
    if f.owner_id != user_id and not is_owner_role:
        raise PermissionDeniedError("只有上传者可以删除文件")
    # Detach all note attachments referencing this file (cascade via FK will clear rows)
    await db.execute(
        NoteAttachment.__table__.delete().where(NoteAttachment.file_id == file_id)
    )
    f.is_deleted = True
    # Remove from disk
    try:
        path = Path(settings.UPLOAD_DIR) / "files" / f.subdir / f.stored_name
        if path.exists():
            os.remove(path)
    except OSError:
        pass  # best-effort cleanup
    await db.commit()


# ── Note attachments ────────────────────────────────────────

async def attach_file_to_note(
    db: AsyncSession, note: Note, file_id: int, role: str, position: int
) -> NoteAttachment:
    """Link an existing file to a note as inline or attachment."""
    f = await get_file(db, file_id)
    att = NoteAttachment(
        note_id=note.id,
        file_id=f.id,
        role=role,
        position=position,
    )
    db.add(att)
    await db.commit()
    await db.refresh(att, attribute_names=["file"])
    return att


async def list_note_attachments(db: AsyncSession, note_id: int) -> list[NoteAttachment]:
    result = await db.execute(
        select(NoteAttachment)
        .options(selectinload(NoteAttachment.file))
        .where(NoteAttachment.note_id == note_id)
        .order_by(NoteAttachment.position, NoteAttachment.id)
    )
    return list(result.scalars().all())


async def detach_attachment(
    db: AsyncSession, attachment_id: int, user_id: int, is_owner_role: bool
) -> None:
    result = await db.execute(
        select(NoteAttachment)
        .options(selectinload(NoteAttachment.note), selectinload(NoteAttachment.file))
        .where(NoteAttachment.id == attachment_id)
    )
    att = result.scalar_one_or_none()
    if att is None:
        raise NotFoundError("附件不存在")
    # Note author OR file uploader OR system owner can detach
    if att.note.author_id != user_id and att.file.owner_id != user_id and not is_owner_role:
        raise PermissionDeniedError("只有笔记作者或文件上传者可以解除附件")
    await db.delete(att)
    await db.commit()