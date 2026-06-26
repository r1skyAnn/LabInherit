"""Tests for /invites endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_redeem_invite_success(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkinvite

    await mkadmin(db_session)
    invite = await mkinvite(db_session, code="REDEEM123")
    resp = await client.post("/api/v1/invites/redeem", json={
        "code": "REDEEM123",
        "email": "newuser@test.com",
        "password": "NewUserPass1",
        "display_name": "新人",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["submitted_email"] == "newuser@test.com"
    assert "注册申请" in data["detail"] or "submitted" in data["detail"].lower()


async def test_redeem_invite_invalid_code(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/invites/redeem", json={
        "code": "NOTEXIST",
        "email": "new@test.com",
        "password": "NewUserPass1",
        "display_name": "新人",
    })
    assert resp.status_code == 404


async def test_redeem_invite_duplicate_email(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkuser, mkinvite

    await mkadmin(db_session)
    await mkuser(db_session, email="dup@test.com", password="Password123")
    invite = await mkinvite(db_session, code="DUPTESTCODE")
    resp = await client.post("/api/v1/invites/redeem", json={
        "code": "DUPTESTCODE",
        "email": "dup@test.com",
        "password": "AnotherPass1",
        "display_name": "重复用户",
    })
    assert resp.status_code == 409


async def test_create_invite_requires_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    member = await mkuser(db_session)
    token_resp = await client.post("/api/v1/auth/login", json={
        "email": member.email,
        "password": "Password123",
    })
    token = token_resp.json()["access_token"]
    resp = await client.post(
        "/api/v1/invites",
        json={"max_uses": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_create_invite_as_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin

    admin = await mkadmin(db_session)
    token_resp = await client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "AdminPass1",
    })
    token = token_resp.json()["access_token"]
    resp = await client.post(
        "/api/v1/invites",
        json={"max_uses": 2, "note": "测试邀请"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["code"]) == 12
    assert data["max_uses"] == 2


async def test_list_invites_as_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkinvite

    admin = await mkadmin(db_session)
    await mkinvite(db_session, code="LISTCODE1")
    await mkinvite(db_session, code="LISTCODE2")
    token_resp = await client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "AdminPass1",
    })
    token = token_resp.json()["access_token"]
    resp = await client.get(
        "/api/v1/invites",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


async def test_revoke_invite(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkinvite

    admin = await mkadmin(db_session)
    invite = await mkinvite(db_session, code="REVOKECODE")
    token_resp = await client.post("/api/v1/auth/login", json={
        "email": admin.email,
        "password": "AdminPass1",
    })
    token = token_resp.json()["access_token"]
    resp = await client.post(
        f"/api/v1/invites/{invite.id}/revoke",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["revoked_at"] is not None
