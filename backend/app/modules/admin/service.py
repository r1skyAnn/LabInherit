"""Admin dashboard aggregation queries."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.modules.users.models import User, UserStatus
from app.modules.projects.models import Project
from app.modules.notes.models import Note
from app.modules.comments.models import Comment, CommentStatus
from app.modules.audit.models import AuditQueue
from app.modules.notifications.models import EmailOutbox, Notification


async def get_dashboard(db: AsyncSession) -> dict:
    # ── KPI queries ──────────────────────
    # User counts by status
    user_counts = {}
    for status in ("active", "graduated", "archived"):
        r = await db.execute(
            select(func.count()).where(User.status == status)
        )
        user_counts[status] = r.scalar_one() or 0

    pending_audits = (await db.execute(
        select(func.count()).where(AuditQueue.status == "pending")
    )).scalar_one() or 0

    open_asks = (await db.execute(
        select(func.count()).where(
            Comment.target_type == "note",
            Comment.is_ask == True,
            Comment.status == CommentStatus.OPEN,
        )
    )).scalar_one() or 0

    stale_threshold = datetime.utcnow() - timedelta(days=settings.STALE_DAYS)
    stale_projects = (await db.execute(
        select(func.count()).where(Project.updated_at < stale_threshold)
    )).scalar_one() or 0

    failed_emails_count = (await db.execute(
        select(func.count()).where(EmailOutbox.status == "failed")
    )).scalar_one() or 0

    notes_total = (await db.execute(
        select(func.count()).select_from(Note)
    )).scalar_one() or 0

    comments_total = (await db.execute(
        select(func.count()).select_from(Comment)
    )).scalar_one() or 0

    kpis = {
        "users": {
            "active": user_counts.get("active", 0),
            "graduated": user_counts.get("graduated", 0),
            "archived": user_counts.get("archived", 0),
        },
        "pending_audits": pending_audits,
        "open_asks": open_asks,
        "stale_projects": stale_projects,
        "failed_emails": failed_emails_count,
        "notes_total": notes_total,
        "comments_total": comments_total,
    }

    # ── Stale projects ──────────────────
    stale_result = await db.execute(
        select(Project)
        .options(selectinload(Project.creator))
        .where(Project.updated_at < stale_threshold)
        .order_by(Project.updated_at.asc())
        .limit(10)
    )
    stale_list = [
        {
            "id": p.id,
            "title": p.title,
            "status": p.status,
            "last_activity_at": p.updated_at,
            "creator_display_name": p.creator.display_name if p.creator else "",
        }
        for p in stale_result.scalars().all()
    ]

    # ── Hot notes ───────────────────────
    hot_result = await db.execute(
        select(Note, Project.title.label("project_title"))
        .join(Project, Note.project_id == Project.id)
        .order_by(Note.like_count.desc(), Note.comment_count.desc())
        .limit(10)
    )
    hot_list = [
        {
            "id": note.id,
            "title": note.title,
            "project_id": note.project_id,
            "project_title": project_title,
            "like_count": note.like_count,
            "comment_count": note.comment_count,
        }
        for note, project_title in hot_result.all()
    ]

    # ── Unanswered asks ────────────────
    ask_result = await db.execute(
        select(Comment, Note.title.label("note_title"), Note.project_id.label("project_id"))
        .join(Note, Comment.target_id == Note.id)
        .where(
            Comment.target_type == "note",
            Comment.is_ask == True,
            Comment.status == CommentStatus.OPEN,
        )
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.desc())
        .limit(20)
    )
    now = datetime.now(tz=timezone.utc)
    ask_list = []
    for c, note_title, project_id in ask_result.all():
        created = c.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        ask_list.append({
            "id": c.id,
            "note_id": c.target_id,
            "project_id": project_id,
            "note_title": note_title,
            "asker_name": c.author.display_name if c.author else "",
            "content": c.content[:200],
            "created_at": c.created_at,
            "days_open": (now - created).days,
        })

    # ── Failed emails ──────────────────
    failed_result = await db.execute(
        select(EmailOutbox)
        .where(EmailOutbox.status == "failed")
        .order_by(EmailOutbox.updated_at.desc())
        .limit(20)
    )
    failed_list = [
        {
            "id": e.id,
            "to_email": e.to_email,
            "subject": e.subject,
            "retry_count": e.retry_count,
            "last_error": e.last_error,
        }
        for e in failed_result.scalars().all()
    ]

    return {
        "kpis": kpis,
        "stale_projects": stale_list,
        "hot_notes": hot_list,
        "unanswered_asks": ask_list,
        "failed_emails": failed_list,
    }


async def update_user_role(
    db: AsyncSession, user_id: int, role: str, actor: User,
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("用户不存在")
    if user.id == actor.id:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("不能修改自己的角色")
    if user.role == "owner" and actor.role != "owner":
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("只有导师可以变更导师角色")
    user.role = role
    await db.commit()
    return user


async def update_user_status(
    db: AsyncSession, user_id: int, status: str, actor: User,
) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("用户不存在")
    if user.id == actor.id:
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("不能修改自己的状态")
    if user.role == "owner" and actor.role != "owner":
        from app.core.exceptions import PermissionDeniedError
        raise PermissionDeniedError("只有导师可以变更导师权限")
    user.status = status
    await db.commit()
    return user
