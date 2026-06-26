"""Pytest configuration: shared fixtures for async SQLAlchemy + SQLite test DB."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.main import app
from app.modules.audit.models import AuditQueue, AuditStatus
from app.modules.invites.models import Invite
from app.modules.users.models import User, UserProfile, UserRole, UserStatus
from app.core.security import hash_password


# ── Test database engine (in-memory SQLite) ────────────────────────────────

_test_engine: AsyncEngine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

_TestSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=_test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """One session per test, auto-creates all tables and drops after."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with _TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """Async HTTP client that uses the test DB session via dependency override."""
    from app.db.session import get_db

    async def _override_get_db() -> AsyncSession:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Factory helpers ─────────────────────────────────────────────────────────

async def mkuser(
    db: AsyncSession,
    *,
    email: str = "test@example.com",
    password: str = "Password123",
    display_name: str = "测试用户",
    status: str = UserStatus.ACTIVE.value,
    role: str = UserRole.MEMBER.value,
) -> User:
    """Create a user with approved audit record."""
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        status=status,
        role=role,
    )
    db.add(user)
    await db.flush()
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    audit = AuditQueue(
        user_id=user.id,
        submitted_payload={"seed": True},
        status=AuditStatus.APPROVED.value,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(user)
    return user


async def mkadmin(db: AsyncSession) -> User:
    return mkuser(
        db,
        email="admin@test.com",
        password="AdminPass1",
        display_name="管理员",
        role=UserRole.ADMIN.value,
    )


async def mkowner(db: AsyncSession) -> User:
    return mkuser(
        db,
        email="owner@test.com",
        password="OwnerPass1",
        display_name="owner",
        role=UserRole.OWNER.value,
    )


async def mkinvite(
    db: AsyncSession,
    *,
    code: str = "TESTCODE123",
    created_by_id: int | None = None,
    max_uses: int = 1,
) -> Invite:
    if created_by_id is None:
        creator = await mkadmin(db)
        created_by_id = creator.id
    invite = Invite(
        code=code,
        created_by=created_by_id,
        max_uses=max_uses,
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    return invite


# ── Reusable pre-built fixtures (member, tokens) ──────────────────────────────

@pytest_asyncio.fixture
async def member(db_session: AsyncSession) -> User:
    """A standard active member user."""
    return await mkuser(db_session, email="member@fixture.test", password="Pass@1234")


@pytest_asyncio.fixture
async def member_token(client: AsyncClient, member: User) -> str:
    """Login token for the standard member."""
    resp = await client.post("/api/v1/auth/login", json={
        "email": member.email,
        "password": "Pass@1234",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, db_session: AsyncSession) -> str:
    """Login token for an admin."""
    admin = await mkadmin(db_session)
    resp = await client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "AdminPass1",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]
