"""Tests for /admin/audit-queue endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


async def test_audit_queue_list_requires_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    member = await mkuser(db_session)
    token = await _get_token(client, member.email, "Password123")
    resp = await client.get(
        "/api/v1/admin/audit-queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_audit_queue_list_as_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin

    admin = await mkadmin(db_session)
    token = await _get_token(client, admin.email, "AdminPass1")
    resp = await client.get(
        "/api/v1/admin/audit-queue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


async def test_approve_pending_user(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkinvite

    admin = await mkadmin(db_session)
    invite = await mkinvite(db_session, code="APPROVETEST")
    admin_token = await _get_token(client, admin.email, "AdminPass1")

    # Register new user via invite
    reg_resp = await client.post("/api/v1/invites/redeem", json={
        "code": "APPROVETEST",
        "email": "toapprove@test.com",
        "password": "NewUserPass1",
        "display_name": "待批准用户",
    })
    assert reg_resp.status_code == 200

    # Find audit entry id
    queue_resp = await client.get(
        "/api/v1/admin/audit-queue?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    items = queue_resp.json()["items"]
    pending_entry = next(i for i in items if i["user_email"] == "toapprove@test.com")

    # Approve
    dec_resp = await client.post(
        f"/api/v1/admin/audit-queue/{pending_entry['id']}/decision",
        json={"action": "approve", "note": "欢迎加入"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["status"] == "approved"

    # Approved user can now login
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "toapprove@test.com",
        "password": "NewUserPass1",
    })
    assert login_resp.status_code == 200


async def test_reject_pending_user(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkadmin, mkinvite

    admin = await mkadmin(db_session)
    invite = await mkinvite(db_session, code="REJECTTEST")
    admin_token = await _get_token(client, admin.email, "AdminPass1")

    await client.post("/api/v1/invites/redeem", json={
        "code": "REJECTTEST",
        "email": "toreject@test.com",
        "password": "RejectPass1",
        "display_name": "待拒绝用户",
    })

    queue_resp = await client.get(
        "/api/v1/admin/audit-queue?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    items = queue_resp.json()["items"]
    pending_entry = next(i for i in items if i["user_email"] == "toreject@test.com")

    dec_resp = await client.post(
        f"/api/v1/admin/audit-queue/{pending_entry['id']}/decision",
        json={"action": "reject", "note": "信息不完整"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert dec_resp.status_code == 200
    assert dec_resp.json()["status"] == "rejected"

    # Rejected user cannot login
    login_resp = await client.post("/api/v1/auth/login", json={
        "email": "toreject@test.com",
        "password": "RejectPass1",
    })
    assert login_resp.status_code == 403
