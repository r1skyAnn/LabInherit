"""Tests for the /auth endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_login_success(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session, email="login@test.com", password="CorrectPass1")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com",
        "password": "CorrectPass1",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0


async def test_login_wrong_password(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    await mkuser(db_session, email="wrongpw@test.com", password="RightPass1")
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wrongpw@test.com",
        "password": "WrongPass",
    })
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "unauthorized"


async def test_login_nonexistent_user(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/login", json={
        "email": "ghost@test.com",
        "password": "anypassword",
    })
    assert resp.status_code == 401


async def test_login_archived_user(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser
    from app.modules.users.models import UserStatus

    user = await mkuser(
        db_session,
        email="archived@test.com",
        password="ArchivedPass1",
        status=UserStatus.ARCHIVED.value,
    )
    resp = await client.post("/api/v1/auth/login", json={
        "email": "archived@test.com",
        "password": "ArchivedPass1",
    })
    assert resp.status_code == 403


async def test_forgot_password_noop(client: AsyncClient) -> None:
    """Unknown emails must return 200 (no user enumeration)."""
    resp = await client.post("/api/v1/auth/forgot-password", json={
        "email": "nobody@example.com",
    })
    assert resp.status_code == 200


async def test_reset_password_bad_token(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": "not.a.valid.token",
        "new_password": "NewPass1234",
    })
    assert resp.status_code == 422
