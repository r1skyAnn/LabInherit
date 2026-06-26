"""Notification + EmailOutbox business logic."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models import EmailOutbox, Notification


async def create_notification(
    db: AsyncSession,
    user_id: int,
    type: str,
    payload: dict | None = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        payload_json=json.dumps(payload) if payload else None,
    )
    db.add(notif)
    await db.commit()
    return notif


async def list_notifications(
    db: AsyncSession,
    user_id: int,
    unread_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Notification], int, int]:
    base = select(Notification).where(Notification.user_id == user_id)
    if unread_only:
        base = base.where(Notification.read_at.is_(None))
    base = base.order_by(Notification.created_at.desc())

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    unread_q = select(func.count()).where(
        Notification.user_id == user_id,
        Notification.read_at.is_(None),
    )
    unread_count = (await db.execute(unread_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    return list(result.scalars().all()), total, unread_count


async def mark_read(db: AsyncSession, notification_id: int, user_id: int) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        raise NotFoundError("通知不存在")
    notif.read_at = datetime.utcnow()
    await db.commit()


async def mark_all_read(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=datetime.utcnow())
    )
    await db.commit()
    return result.rowcount


async def get_unread_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count()).where(
            Notification.user_id == user_id,
            Notification.read_at.is_(None),
        )
    )
    return result.scalar_one() or 0


# ── EmailOutbox helpers ──────────────────────────────────────


async def create_email_outbox(
    db: AsyncSession,
    to_email: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
    related_type: str | None = None,
    related_id: int | None = None,
) -> EmailOutbox:
    entry = EmailOutbox(
        to_email=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        related_type=related_type,
        related_id=related_id,
    )
    db.add(entry)
    await db.commit()
    return entry
