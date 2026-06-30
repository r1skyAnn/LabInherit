"""Guide HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser
from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.db.session import get_db
from app.modules.files import service as files_service
from app.modules.files.schemas import FileOut
from app.modules.guides import service
from app.modules.guides.models import Guide, GuideAttachment
from app.modules.guides.schemas import (
    AttachmentCreate,
    AttachmentUpdate,
    GuideAttachmentOut,
    GuideCreate,
    GuideListResponse,
    GuideOut,
    GuideUpdate,
)

router = APIRouter(prefix="/guides", tags=["guides"])


def _can_create(user) -> bool:
    if user.role == "owner": return True
    if user.is_owner(): return True
    if user.status == "graduated": return True
    if user.profile and user.profile.enrollment_year:
        from datetime import datetime
        return datetime.utcnow().year - user.profile.enrollment_year >= 2
    return False


def _can_update(user) -> bool:
    if user.role == "owner": return True
    if user.is_owner(): return True
    if user.status == "graduated": return False
    if user.profile and user.profile.enrollment_year:
        from datetime import datetime
        return datetime.utcnow().year - user.profile.enrollment_year >= 2
    return False


def _build_out(guide) -> GuideOut:
    return GuideOut(
        id=guide.id,
        title=guide.title,
        slug=guide.slug,
        content=guide.content,
        tag=guide.tag,
        related_projects=guide.related_projects,
        sort_order=guide.sort_order,
        is_pinned=guide.is_pinned,
        author_id=guide.author_id,
        author_name=guide.author.display_name if guide.author else "",
        created_at=guide.created_at,
        updated_at=guide.updated_at,
    )


def _att_to_out(att: GuideAttachment) -> GuideAttachmentOut:
    return GuideAttachmentOut(
        id=att.id,
        guide_id=att.guide_id,
        file_id=att.file_id,
        role=att.role,
        position=att.position,
        created_at=att.created_at,
        file=FileOut.model_validate(files_service.file_to_out(att.file)),
    )


@router.get("", response_model=GuideListResponse, summary="列出指南")
async def list_guides(
    db: Annotated[AsyncSession, Depends(get_db)],
    tag: str | None = Query(None),
) -> GuideListResponse:
    items = await service.list_guides(db, tag=tag)
    return GuideListResponse(items=[_build_out(g) for g in items], total=len(items))


@router.get("/{slug}", response_model=GuideOut, summary="获取指南详情")
async def get_guide(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    guide = await service.get_guide(db, slug)
    return _build_out(guide)


@router.post("", response_model=GuideOut, summary="创建指南")
async def create_guide(
    payload: GuideCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    if not _can_create(user):
        raise PermissionDeniedError("只有导师、师兄（入学2年以上）或已毕业成员可以创建指南")
    guide = await service.create_guide(db, author_id=user.id, data=payload.model_dump(exclude_unset=True))
    return _build_out(guide)


@router.patch("/{guide_id}", response_model=GuideOut, summary="更新指南")
async def update_guide(
    guide_id: int,
    payload: GuideUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideOut:
    if not _can_update(user):
        raise PermissionDeniedError("毕业成员只能添加不能修改，导师和师兄可以编辑")
    guide = await service.update_guide(db, guide_id, user.id, _can_update(user), payload.model_dump(exclude_unset=True))
    return _build_out(guide)


@router.delete("/{guide_id}", summary="删除指南")
async def delete_guide(
    guide_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    if user.role != "owner":
        raise PermissionDeniedError("只有导师可以删除指南")
    await service.delete_guide(db, guide_id, user.id, True)
    return {"detail": "已删除"}


# ── Guide attachments (mirrors /files/notes/{note_id}/attachments) ──────────


@router.get(
    "/{guide_id}/attachments",
    response_model=list[GuideAttachmentOut],
    summary="列出指南的所有附件",
)
async def list_guide_attachments(
    guide_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[GuideAttachmentOut]:
    guide = await db.get(Guide, guide_id)
    if guide is None:
        raise NotFoundError("指南不存在")
    res = await db.execute(
        select(GuideAttachment)
        .options(selectinload(GuideAttachment.file))
        .where(GuideAttachment.guide_id == guide_id)
        .order_by(GuideAttachment.position, GuideAttachment.created_at)
    )
    return [_att_to_out(a) for a in res.scalars().all()]


@router.post(
    "/{guide_id}/attachments",
    response_model=GuideAttachmentOut,
    summary="把已上传的文件附加到指南",
)
async def add_guide_attachment(
    guide_id: int,
    payload: AttachmentCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideAttachmentOut:
    guide = await db.get(Guide, guide_id)
    if guide is None:
        raise NotFoundError("指南不存在")
    # Only guide author or owner-role can attach
    if guide.author_id != user.id and not user.is_owner() and user.role != "owner":
        raise PermissionDeniedError("只有指南作者可以附加文件")
    # Verify file exists
    file = await files_service.get_file(db, payload.file_id)
    att = GuideAttachment(
        guide_id=guide_id,
        file_id=file.id,
        role=payload.role,
        position=payload.position,
    )
    db.add(att)
    await db.commit()
    res = await db.execute(
        select(GuideAttachment)
        .options(selectinload(GuideAttachment.file))
        .where(GuideAttachment.id == att.id)
    )
    return _att_to_out(res.scalar_one())


@router.patch(
    "/{guide_id}/attachments/{attachment_id}",
    response_model=GuideAttachmentOut,
    summary="更新附件的 role / position",
)
async def update_guide_attachment(
    guide_id: int,
    attachment_id: int,
    payload: AttachmentUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GuideAttachmentOut:
    res = await db.execute(
        select(GuideAttachment)
        .options(selectinload(GuideAttachment.file))
        .where(
            GuideAttachment.id == attachment_id,
            GuideAttachment.guide_id == guide_id,
        )
    )
    att = res.scalar_one_or_none()
    if att is None:
        raise NotFoundError("附件不存在")
    guide = await db.get(Guide, guide_id)
    if guide is None or (
        guide.author_id != user.id
        and not user.is_owner()
        and user.role != "owner"
    ):
        raise PermissionDeniedError("无权编辑此附件")
    if payload.role is not None:
        att.role = payload.role
    if payload.position is not None:
        att.position = payload.position
    await db.commit()
    await db.refresh(att, attribute_names=["file"])
    return _att_to_out(att)


@router.delete(
    "/{guide_id}/attachments/{attachment_id}",
    summary="从指南中移除附件（不删除物理文件）",
)
async def remove_guide_attachment(
    guide_id: int,
    attachment_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    res = await db.execute(
        select(GuideAttachment).where(
            GuideAttachment.id == attachment_id,
            GuideAttachment.guide_id == guide_id,
        )
    )
    att = res.scalar_one_or_none()
    if att is None:
        raise NotFoundError("附件不存在")
    guide = await db.get(Guide, guide_id)
    if guide is None or (
        guide.author_id != user.id
        and not user.is_owner()
        and user.role != "owner"
    ):
        raise PermissionDeniedError("无权移除此附件")
    await db.delete(att)
    await db.commit()
    return {"detail": "附件已移除"}
