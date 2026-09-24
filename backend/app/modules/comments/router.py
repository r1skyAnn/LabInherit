"""Comment HTTP routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser
from app.db.session import get_db
from app.modules.comments import service
from app.modules.comments.schemas import (
    CommentCreate,
    CommentListResponse,
    CommentOut,
    CommentUpdate,
)

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/notes/{note_id}", response_model=CommentListResponse, summary="获取笔记评论列表")
async def list_note_comments(
    note_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> CommentListResponse:
    items, total = await service.list_comments(
        db, target_type="note", target_id=note_id, page=page, page_size=page_size,
    )
    return CommentListResponse(items=[CommentOut.model_validate(c) for c in items], total=total)


@router.post("/notes/{note_id}", response_model=CommentOut, summary="添加评论/追问")
async def create_note_comment(
    note_id: int,
    payload: CommentCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CommentOut:
    comment = await service.create_comment(
        db, author_id=user.id, target_type="note", target_id=note_id,
        data=payload.model_dump(exclude_unset=True),
    )
    # Fire side effects: notification + email for the note author
    _ = await _fire_comment_side_effects(db, comment, user)
    return CommentOut.model_validate(comment)


@router.get("/projects/{project_id}", response_model=CommentListResponse, summary="获取项目下所有追问")
async def list_project_asks(
    project_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> CommentListResponse:
    items, total = await service.list_asks_for_project(
        db, project_id=project_id, page=page, page_size=page_size,
    )
    return CommentListResponse(items=[CommentOut.model_validate(c) for c in items], total=total)


@router.patch("/{comment_id}", response_model=CommentOut, summary="编辑评论/改状态/升级追问")
async def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CommentOut:
    data = payload.model_dump(exclude_unset=True)
    comment = await service.update_comment(
        db, comment_id, user.id, user.is_owner(), data,
    )
    # If this was an upgrade to ask, fire email notification
    if data.get("is_ask"):
        _ = await _fire_ask_upgrade_side_effects(db, comment, user)
    return CommentOut.model_validate(comment)


@router.delete("/{comment_id}", summary="删除评论")
async def delete_comment(
    comment_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    await service.delete_comment(db, comment_id, user.id, user.is_owner())
    return {"detail": "评论已删除"}


async def _fire_comment_side_effects(db: AsyncSession, comment, author):
    """Create notification + email_outbox entry for new comment on a note."""
    from app.modules.notes.service import get_note
    note = await get_note(db, comment.target_id)
    if note is None or note.author_id == author.id:
        return

    from app.modules.notifications.service import create_notification
    await create_notification(
        db,
        user_id=note.author_id,
        type="ask_opened" if comment.status == "open" else "comment",
        payload={
            "comment_id": comment.id,
            "note_id": note.id,
            "project_id": note.project_id,
            "note_title": note.title,
            "commenter_name": author.display_name,
            "content": comment.content[:100],
        },
    )

    from app.modules.notifications.service import create_email_outbox
    await create_email_outbox(
        db,
        to_email=note.author_email,
        subject=f"有人在你的笔记《{note.title}》留言了",
        body_text=(
            f"{author.display_name} 在你的笔记《{note.title}》下留言：\n\n"
            f"{comment.content[:300]}\n\n"
            f"查看详情：{_frontend_url(note.project_id, note.id)}"
        ),
        related_type="comment",
        related_id=comment.id,
    )


async def _fire_ask_upgrade_side_effects(db: AsyncSession, comment, upgrader):
    """Fire email when a regular comment is upgraded to an ask."""
    from app.modules.notes.service import get_note
    note = await get_note(db, comment.target_id)
    if note is None or note.author_id == upgrader.id:
        return

    from app.modules.notifications.service import create_notification, create_email_outbox
    await create_notification(
        db,
        user_id=note.author_id,
        type="ask_opened",
        payload={
            "comment_id": comment.id,
            "note_id": note.id,
            "project_id": note.project_id,
            "note_title": note.title,
            "commenter_name": upgrader.display_name,
            "content": comment.content[:100],
        },
    )
    await create_email_outbox(
        db,
        to_email=note.author_email,
        subject=f"有人在你的笔记《{note.title}》追问了",
        body_text=(
            f"{upgrader.display_name} 在你的笔记《{note.title}》将一条评论升级为了追问：\n\n"
            f"{comment.content[:300]}\n\n"
            f"查看详情：{_frontend_url(note.project_id, note.id)}"
        ),
        related_type="comment",
        related_id=comment.id,
    )


def _frontend_url(project_id: int, note_id: int) -> str:
    from app.core.config import settings
    return f"{settings.APP_BASE_URL}/projects/{project_id}/notes/{note_id}"
