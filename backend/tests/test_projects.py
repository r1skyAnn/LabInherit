"""Tests for /projects endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return resp.json()["access_token"]


async def test_create_project_as_member(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    resp = await client.post(
        "/api/v1/projects",
        json={"title": "测试项目", "description": "一个测试项目", "priority": "high"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "测试项目"
    assert data["created_by"] == user.id
    assert data["creator_display_name"] == user.display_name


async def test_create_project_as_graduated_fails(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser
    from app.modules.users.models import UserStatus

    grad = await mkuser(
        db_session,
        email="grad@test.com",
        status=UserStatus.GRADUATED.value,
    )
    token = await _get_token(client, grad.email, "Password123")
    resp = await client.post(
        "/api/v1/projects",
        json={"title": "毕业项目"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


async def test_list_projects(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    # Create 2 projects
    for i in range(2):
        await client.post(
            "/api/v1/projects",
            json={"title": f"项目{i}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    resp = await client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2


async def test_list_projects_filter_by_status(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    await client.post(
        "/api/v1/projects",
        json={"title": "进行中项目"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get("/api/v1/projects?status=active")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["status"] == "active"


async def test_get_project(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "查看项目"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "查看项目"


async def test_get_project_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/projects/99999")
    assert resp.status_code == 404


async def test_update_project_as_owner(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "原始标题"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}",
        json={"title": "新标题", "status": "completed"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"
    assert resp.json()["status"] == "completed"


async def test_update_project_as_non_owner_fails(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    owner = await mkuser(db_session, email="owner@test.com")
    other = await mkuser(db_session, email="other@test.com")

    owner_token = await _get_token(client, owner.email, "Password123")
    other_token = await _get_token(client, other.email, "Password123")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "别人的项目"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}",
        json={"title": "我来改"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


async def test_update_project_as_admin(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser, mkadmin

    user = await mkuser(db_session)
    admin = await mkadmin(db_session)

    user_token = await _get_token(client, user.email, "Password123")
    admin_token = await _get_token(client, admin.email, "AdminPass1")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "成员的项目"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}",
        json={"status": "paused"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paused"


async def test_delete_project_as_owner(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "要删除的项目"},
        headers={"Authorization": f"Bearer {token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Verify deletion
    get_resp = await client.get(f"/api/v1/projects/{pid}")
    assert get_resp.status_code == 404


async def test_delete_project_as_non_owner_fails(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    owner = await mkuser(db_session, email="owner2@test.com")
    other = await mkuser(db_session, email="other2@test.com")

    owner_token = await _get_token(client, owner.email, "Password123")
    other_token = await _get_token(client, other.email, "Password123")

    create_resp = await client.post(
        "/api/v1/projects",
        json={"title": "不可删除"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    pid = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403
