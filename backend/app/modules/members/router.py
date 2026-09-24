"""Member list HTTP routes (owner only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, require_active_member
from app.db.session import get_db
from app.modules.members import service
from app.modules.members.schemas import MemberListResponse, MemberOut
from app.modules.users.models import User

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=MemberListResponse, summary="成员列表（成员及以上）")
async def list_members(
    _: Annotated[User, Depends(require_active_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    search: str | None = Query(None),
) -> MemberListResponse:
    from app.modules.users.models import UserProfile  # avoid circular at module load

    base = (
        select(User)
        .options(
            # loaded via selectinload below
        )
        .order_by(User.created_at.desc())
    )
    if search:
        base = base.where(
            User.display_name.ilike(f"%{search}%")
            | User.email.ilike(f"%{search}%")
        )

    count_q = select(func.count()).select_from(User)
    if search:
        count_q = count_q.where(
            User.display_name.ilike(f"%{search}%")
            | User.email.ilike(f"%{search}%")
        )
    total = (await db.execute(count_q)).scalar_one() or 0

    offset = (page - 1) * page_size
    result = await db.execute(base.offset(offset).limit(page_size))
    users = list(result.scalars().all())

    # Bulk load profiles
    user_ids = [u.id for u in users]
    profiles_map: dict[int, UserProfile | None] = {}
    if user_ids:
        profile_result = await db.execute(
            select(UserProfile).where(UserProfile.user_id.in_(user_ids))
        )
        for profile in profile_result.scalars().all():
            profiles_map[profile.user_id] = profile

    items = []
    for user in users:
        profile = profiles_map.get(user.id)
        items.append(_member_out(user, profile))

    return MemberListResponse(items=items, total=total)


def _member_out(user, profile=None) -> MemberOut:
    p = profile or (user.profile if hasattr(user, 'profile') else None)
    return MemberOut(
        id=user.id,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        status=user.status,
        enrollment_year=p.enrollment_year if p else None,
        graduation_year=p.graduation_year if p else None,
        research_direction=p.research_direction if p else None,
        current_affiliation=p.current_affiliation if p else None,
        bio=p.bio if p else None,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get("/{user_id}", response_model=MemberOut, summary="获取成员详情（成员及以上）")
async def get_member(
    user_id: int,
    _: Annotated[User, Depends(require_active_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MemberOut:
    user = await service.get_member(db, user_id)
    return _member_out(user)
