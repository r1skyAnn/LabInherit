"""File HTTP routes — upload, download, attach to notes."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentUser
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.modules.files import service
from app.modules.files.models import File
from app.modules.files.schemas import (
    AttachmentCreate,
    AttachmentUpdate,
    FileOut,
    NoteAttachmentOut,
)
from app.modules.notes.models import Note
from sqlalchemy import select

router = APIRouter(prefix="/files", tags=["files"])


# ── File operations ──────────────────────────────────────────

@router.post("/upload", response_model=FileOut, summary="上传文件")
async def upload_file(
    file: UploadFile,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: int | None = Form(None),
) -> FileOut:
    """通用文件上传。返回的 file 可用于附加到笔记 / 头像 / 评论图片等。"""
    record = await service.save_upload(db, user, file, project_id)
    return FileOut.model_validate(service.file_to_out(record))


@router.get("/{file_id}", response_model=FileOut, summary="获取文件元信息")
async def get_file_meta(
    file_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileOut:
    f = await service.get_file(db, file_id)
    return FileOut.model_validate(service.file_to_out(f))


@router.api_route(
    "/{file_id}/download",
    methods=["GET", "HEAD"],
    summary="下载文件（强制附件文件名）",
)
async def download_file(
    file_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    # Public — anyone with the link can download (matches existing /uploads/* behaviour)
) -> FileResponse:
    f = await service.get_file(db, file_id)
    path = Path(settings.UPLOAD_DIR) / "files" / f.subdir / f.stored_name
    if not path.exists():
        raise NotFoundError("物理文件已丢失")
    # RFC 5987 — encode original (possibly CJK) filename
    from urllib.parse import quote
    encoded = quote(f.original_name, safe="")
    return FileResponse(
        path=str(path),
        media_type=f.mime_type,
        filename=f.original_name,
        headers={
            "Content-Disposition": (
                f"attachment; filename=\"{encoded}\"; "
                f"filename*=UTF-8''{encoded}"
            ),
        },
    )


@router.delete("/{file_id}", summary="删除文件")
async def delete_file(
    file_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_file(db, file_id, user.id, user.is_owner())
    return {"detail": "文件已删除"}


# ── Note attachments ─────────────────────────────────────────

@router.get(
    "/notes/{note_id}/attachments",
    response_model=list[NoteAttachmentOut],
    summary="列出笔记的所有附件",
)
async def list_attachments(
    note_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[NoteAttachmentOut]:
    # Confirm note exists
    note_res = await db.execute(select(Note).where(Note.id == note_id))
    if note_res.scalar_one_or_none() is None:
        raise NotFoundError("笔记不存在")
    atts = await service.list_note_attachments(db, note_id)
    return [
        NoteAttachmentOut(
            id=a.id, note_id=a.note_id, file_id=a.file_id,
            role=a.role, position=a.position, created_at=a.created_at,
            file=FileOut.model_validate(service.file_to_out(a.file)),
        )
        for a in atts
    ]


@router.post(
    "/notes/{note_id}/attachments",
    response_model=NoteAttachmentOut,
    summary="把已上传的文件附加到笔记",
)
async def add_attachment(
    note_id: int,
    payload: AttachmentCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteAttachmentOut:
    note_res = await db.execute(select(Note).where(Note.id == note_id))
    note = note_res.scalar_one_or_none()
    if note is None:
        raise NotFoundError("笔记不存在")
    if note.author_id != user.id and not user.is_owner():
        raise PermissionDeniedError("只有笔记作者可以附加文件")
    att = await service.attach_file_to_note(
        db, note, payload.file_id, payload.role, payload.position
    )
    return NoteAttachmentOut(
        id=att.id, note_id=att.note_id, file_id=att.file_id,
        role=att.role, position=att.position, created_at=att.created_at,
        file=FileOut.model_validate(service.file_to_out(att.file)),
    )


@router.patch(
    "/notes/{note_id}/attachments/{attachment_id}",
    response_model=NoteAttachmentOut,
    summary="更新附件的 role / position",
)
async def update_attachment(
    note_id: int,
    attachment_id: int,
    payload: AttachmentUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> NoteAttachmentOut:
    res = await db.execute(
        select(NoteAttachment)
        .options(selectinload(NoteAttachment.file))
        .where(NoteAttachment.id == attachment_id, NoteAttachment.note_id == note_id)
    )
    att = res.scalar_one_or_none()
    if att is None:
        raise NotFoundError("附件不存在")
    # Permission: note author or owner-role can edit
    note_res = await db.execute(select(Note).where(Note.id == note_id))
    note = note_res.scalar_one_or_none()
    if note is None or (note.author_id != user.id and not user.is_owner()):
        raise PermissionDeniedError("无权编辑此附件")
    if payload.role is not None:
        att.role = payload.role
    if payload.position is not None:
        att.position = payload.position
    await db.commit()
    await db.refresh(att, attribute_names=["file"])
    return NoteAttachmentOut(
        id=att.id, note_id=att.note_id, file_id=att.file_id,
        role=att.role, position=att.position, created_at=att.created_at,
        file=FileOut.model_validate(service.file_to_out(att.file)),
    )


@router.delete(
    "/notes/{note_id}/attachments/{attachment_id}",
    summary="从笔记中移除附件（不删除物理文件）",
)
async def remove_attachment(
    note_id: int,
    attachment_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.detach_attachment(db, attachment_id, user.id, user.is_owner())
    return {"detail": "附件已移除"}