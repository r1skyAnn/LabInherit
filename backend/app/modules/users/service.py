"""User profile business logic."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User, UserProfile


async def get_me(user: User) -> User:
    return user


async def update_me(db: AsyncSession, user: User, data: dict) -> User:
    if "display_name" in data:
        user.display_name = data["display_name"]

    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        user.profile = profile

    profile_updates = {
        "enrollment_year", "graduation_year",
        "research_direction", "current_affiliation", "bio", "avatar_url",
    }
    for field in profile_updates:
        if field in data:
            setattr(profile, field, data[field])

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    old_password: str,
    new_password: str,
) -> None:
    if not verify_password(old_password, user.password_hash):
        raise ValidationError("旧密码不正确")
    if len(new_password) < 8:
        raise ValidationError("新密码至少需要 8 个字符")
    user.password_hash = hash_password(new_password)
    db.add(user)
    await db.commit()
