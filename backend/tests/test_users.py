"""Tests for /api/v1/users endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.modules.users.models import User


@pytest.mark.asyncio
async def test_update_me(client: AsyncClient, member_token: str) -> None:
    resp = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"display_name": "新名字"},
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "新名字"


@pytest.mark.asyncio
async def test_update_me_profile(client: AsyncClient, member_token: str) -> None:
    resp = await client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {member_token}"},
        json={
            "display_name": "更新资料",
            "research_direction": "计算机视觉",
            "enrollment_year": 2023,
        },
    )
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["research_direction"] == "计算机视觉"
    assert profile["enrollment_year"] == 2023


@pytest.mark.asyncio
async def test_change_password_success(client: AsyncClient, member: User, member_token: str) -> None:
    resp = await client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"old_password": "Pass@1234", "new_password": "NewPass@123"},
    )
    assert resp.status_code == 200

    # Verify new password works
    login = await client.post("/api/v1/auth/login", json={
        "email": member.email,
        "password": "NewPass@123",
    })
    assert login.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_old(client: AsyncClient, member_token: str) -> None:
    resp = await client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"old_password": "wrong", "new_password": "NewPass@123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_change_password_too_short(client: AsyncClient, member_token: str) -> None:
    resp = await client.post(
        "/api/v1/users/me/change-password",
        headers={"Authorization": f"Bearer {member_token}"},
        json={"old_password": "Pass@1234", "new_password": "short"},
    )
    assert resp.status_code == 422
