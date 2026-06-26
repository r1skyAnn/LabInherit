"""Tests for /projects/{id}/categories endpoints."""

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


async def test_create_root_category(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "深度学习"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "深度学习"
    assert data["parent_id"] is None
    assert data["path"] == str(data["id"])
    assert len(data["children"]) == 0


async def test_create_child_category(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    root_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "计算机视觉"},
        headers={"Authorization": f"Bearer {token}"},
    )
    root_id = root_resp.json()["id"]

    child_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "目标检测", "parent_id": root_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert child_resp.status_code == 200
    data = child_resp.json()
    assert data["parent_id"] == root_id
    assert data["path"] == f"{root_id}/{data['id']}"


async def test_create_duplicate_slug_in_same_parent_fails(
    client: AsyncClient, db_session
) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "NLP"},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "NLP"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 409


async def test_list_categories_as_tree(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    root_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "方法"},
        headers={"Authorization": f"Bearer {token}"},
    )
    root_id = root_resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "监督学习", "parent_id": root_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(f"/api/v1/projects/{pid}/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    items = data["items"]
    assert len(items) == 1  # Only root at top level
    assert items[0]["name"] == "方法"
    assert len(items[0]["children"]) == 1
    assert items[0]["children"][0]["name"] == "监督学习"


async def test_get_category(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "强化学习"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cid = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/projects/{pid}/categories/{cid}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "强化学习"


async def test_update_category_rename(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    create_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "旧名称"},
        headers={"Authorization": f"Bearer {token}"},
    )
    cid = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/v1/projects/{pid}/categories/{cid}",
        json={"name": "新名称"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "新名称"


async def test_delete_category_cascades_children(client: AsyncClient, db_session) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")
    pid = await _create_project(client, token)

    root_resp = await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "待删除"},
        headers={"Authorization": f"Bearer {token}"},
    )
    root_id = root_resp.json()["id"]

    await client.post(
        f"/api/v1/projects/{pid}/categories",
        json={"name": "子分类", "parent_id": root_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    del_resp = await client.delete(
        f"/api/v1/projects/{pid}/categories/{root_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 200

    # Child should be cascade-deleted
    get_resp = await client.get(f"/api/v1/projects/{pid}/categories")
    assert get_resp.json()["total"] == 0


async def test_different_projects_have_independent_trees(
    client: AsyncClient, db_session
) -> None:
    from tests.conftest import mkuser

    user = await mkuser(db_session)
    token = await _get_token(client, user.email, "Password123")

    pid1 = await _create_project(client, token, "项目A")
    pid2 = await _create_project(client, token, "项目B")

    await client.post(
        f"/api/v1/projects/{pid1}/categories",
        json={"name": "A的分类"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        f"/api/v1/projects/{pid2}/categories",
        json={"name": "B的分类"},
        headers={"Authorization": f"Bearer {token}"},
    )

    resp1 = await client.get(f"/api/v1/projects/{pid1}/categories")
    resp2 = await client.get(f"/api/v1/projects/{pid2}/categories")

    assert resp1.json()["total"] == 1
    assert resp2.json()["total"] == 1
    assert resp1.json()["items"][0]["name"] != resp2.json()["items"][0]["name"]
