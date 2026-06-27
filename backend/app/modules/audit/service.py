"""Audit-queue business logic."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.modules.audit.models import AuditQueue, AuditStatus
from app.modules.audit.schemas import AuditEntryOut
from app.modules.users.models import User, UserStatus


async def list_queue(
    db: AsyncSession,
    _: User,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditEntryOut], int]:
    """Return paginated audit entries with joined user/reviewer info."""
    base = (
        select(AuditQueue)
        .options(
            selectinload(AuditQueue.user),
            selectinload(AuditQueue.reviewer),
        )
        .order_by(AuditQueue.created_at.desc())
    )
    if status:
        base = base.where(AuditQueue.status == status)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(
        base.offset(offset).limit(page_size)
    )
    rows = result.scalars().all()

    # Eager-load users
    out = []
    for entry in rows:
        user_email = ""
        user_display_name = ""
        reviewer_email = None
        if entry.user:
            user_email = entry.user.email
            user_display_name = entry.user.display_name
        if entry.reviewer:
            reviewer_email = entry.reviewer.email
        out.append(AuditEntryOut(
            id=entry.id,
            user_id=entry.user_id,
            user_email=user_email,
            user_display_name=user_display_name,
            submitted_payload=entry.submitted_payload or {},
            reviewer_id=entry.reviewer_id,
            reviewer_email=reviewer_email,
            status=entry.status,
            decision_note=entry.decision_note,
            decided_at=entry.decided_at,
            created_at=entry.created_at,
        ))
    return out, total


async def decide(
    db: AsyncSession,
    entry_id: int,
    reviewer: User,
    action: str,
    note: str | None = None,
) -> AuditEntryOut:
    if not reviewer.is_admin_or_above():
        raise PermissionDeniedError("只有管理员可以审核")

    result = await db.execute(
        select(AuditQueue)
        .options(selectinload(AuditQueue.user), selectinload(AuditQueue.reviewer))
        .where(AuditQueue.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise NotFoundError("审核条目不存在")

    if entry.status != AuditStatus.PENDING.value:
        raise ConflictError("该申请已被处理")

    if action == "approve":
        user_result = await db.execute(select(User).where(User.id == entry.user_id))
        user = user_result.scalar_one_or_none()
        if user is not None:
            user.status = UserStatus.ACTIVE.value
        entry.status = AuditStatus.APPROVED.value
    elif action == "reject":
        entry.status = AuditStatus.REJECTED.value
        user_result = await db.execute(select(User).where(User.id == entry.user_id))
        user = user_result.scalar_one_or_none()
        if user is not None:
            user.status = UserStatus.ARCHIVED.value
    else:
        raise ConflictError("action 必须是 approve 或 reject")

    entry.reviewer_id = reviewer.id
    entry.decision_note = note
    entry.decided_at = datetime.now(tz=timezone.utc)

    await db.commit()
    await db.refresh(entry)

    return AuditEntryOut(
        id=entry.id,
        user_id=entry.user_id,
        user_email=entry.user.email if entry.user else "",
        user_display_name=entry.user.display_name if entry.user else "",
        submitted_payload=entry.submitted_payload or {},
        reviewer_id=entry.reviewer_id,
        reviewer_email=entry.reviewer.email if entry.reviewer else None,
        status=entry.status,
        decision_note=entry.decision_note,
        decided_at=entry.decided_at,
        created_at=entry.created_at,
    )
