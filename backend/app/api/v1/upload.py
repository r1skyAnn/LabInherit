"""File upload endpoint — images + PDFs, organized by project/note or showcase."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile
from app.core.exceptions import ValidationError

from app.core.config import settings
from app.core.deps import get_current_user
from app.modules.users.models import User

ALLOWED_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp", "application/pdf"}
MAX_SIZE = 20 * 1024 * 1024  # 20 MB

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", summary="上传文件")
async def upload_image(
    file: UploadFile,
    project_id: int = Form(0),
    note_id: int | None = Form(None),
    _: Annotated[User, Depends(get_current_user)] = None,
) -> dict:
    if file.content_type not in ALLOWED_TYPES:
        raise ValidationError("仅支持 PNG / JPEG / GIF / WebP / PDF 格式")

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise ValidationError("文件不能超过 20 MB")

    suffix = Path(file.filename or "file").suffix.lstrip(".") or "bin"
    name = f"{uuid.uuid4().hex}.{suffix}"

    base = Path(settings.UPLOAD_DIR)
    if note_id and project_id:
        target_dir = base / str(project_id) / str(note_id)
    elif project_id:
        target_dir = base / str(project_id)
    else:
        target_dir = base / "showcase"

    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / name).write_bytes(contents)

    url = f"/uploads/{target_dir.relative_to(base).as_posix()}/{name}"
    return {"url": url}
