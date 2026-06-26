"""Tests for /notes endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _get_token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return resp.json()["access_token"]


async def _create_project(client: AsyncClient, token: str, title: str = "测试项目") -> int:
    resp = await client.post(
        "/api/v1/projects",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp.json()["id"]


async def test_create_note(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    resp = await client.post(
        "/api/v1/notes",
        json={
            "project_id": pid,
            "title": "环境配置指南",
            "content": "# 安装\n## 步骤1\n安装 Python 依赖。",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "环境配置指南"
    assert data["author_id"] == user.id
    assert data["author_display_name"] == user.display_name
    assert data["author_email"] == user.email
    assert data["author_enrollment_year"] == user.profile.enrollment_year


async def test_list_notes_by_project(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid1 = await _create_project(client, token, "项目A")
    pid2 = await _create_project(client, token, "项目B")

    await client.post(
        "/api/v1/notes",
        json={"project_id": pid1, "title": "A的笔记"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/notes",
        json={"project_id": pid2, "title": "B的笔记"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"/api/v1/notes?project_id={pid1}")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "A的笔记"


async def test_search_notes(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "PyTorch安装"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "TensorFlow配置"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"/api/v1/notes?project_id={pid}&q=PyTorch")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["items"][0]["title"] == "PyTorch安装"


async def test_get_note(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "调参记录"},
        headers={"Authorization": f"Bearer {token}"},
    )
    nid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/notes/{nid}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "调参记录"


async def test_update_note_as_author(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "旧标题", "content": "旧内容"},
        headers={"Authorization": f"Bearer {token}"},
    )
    nid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/notes/{nid}",
        json={"title": "新标题", "content": "新内容"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"


async def test_update_note_as_non_author_fails(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    author = await mkuser(db_session, email="author@test.com")
    other = await mkuser(db_session, email="other@test.com")

    author_token = await _get_token(client, author.email, "Password123")
    other_token = await _get_token(client, other.email, "Password123")
    pid = await _create_project(client, author_token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "我的笔记"},
        headers={"Authorization": f"Bearer {author_token}"},
    )
    nid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/notes/{nid}",
        json={"title": "我要改"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert resp.status_code == 403


async def test_delete_note(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "待删除"},
        headers={"Authorization": f"Bearer {token}"},
    )
    nid = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/notes/{nid}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    get_resp = await client.get(f"/api/v1/notes/{nid}")
    assert get_resp.status_code == 404


async def test_like_note(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "好笔记"},
        headers={"Authorization": f"Bearer {token}"},
    )
    nid = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/notes/{nid}/like")
    assert resp.status_code == 200
    assert resp.json()["like_count"] == 1

    resp2 = await client.post(f"/api/v1/notes/{nid}/like")
    assert resp2.json()["like_count"] == 2


async def test_note_author_snapshot_preserved(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        "/api/v1/notes",
        json={"project_id": pid, "title": "快照测试"},
        headers={"Authorization": f"Bearer {token}"},
    )
    nid = create_resp.json()["id"]
    data = create_resp.json()
    assert data["author_display_name"] == user.display_name
    assert data["author_email"] == user.email

    # Even after fetching again, the snapshot remains
    get_resp = await client.get(f"/api/v1/notes/{nid}")
    assert get_resp.json()["author_display_name"] == user.display_name
    assert get_resp.json()["author_email"] == user.email
