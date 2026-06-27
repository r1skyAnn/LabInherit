"""Seed script — populates the database with demo data for S1 testing.

Usage:
    cd backend
    uv run python -m app.scripts.seed

Run AFTER `alembic upgrade head`.
"""

from __future__ import annotations

import asyncio
import secrets
import sys
from datetime import datetime, timezone

# Ensure the app package is importable
sys.path.insert(0, ".")

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.modules.audit.models import AuditQueue, AuditStatus
from app.modules.invites.models import Invite
from app.modules.users.models import User, UserProfile, UserRole, UserStatus


async def _seed() -> None:
    print("\n" + "=" * 60)
    print("🌱  LabInherit — S1 Demo Seed Data")
    print("=" * 60)

    async with AsyncSessionLocal() as db:
        # ── 1. Owner ──────────────────────────────────────────────────────
        owner = User(
            email="owner@labinherit.local",
            password_hash=hash_password("Owner@123"),
            display_name="实验室导师",
            status=UserStatus.ACTIVE.value,
            role=UserRole.OWNER.value,
        )
        db.add(owner)
        await db.flush()
        owner_profile = UserProfile(
            user_id=owner.id,
            enrollment_year=2020,
            graduation_year=None,
            research_direction="实验室管理",
            current_affiliation="某某大学",
            bio="实验室 PI，创立 LabInherit 平台。",
        )
        db.add(owner_profile)

        # Owner auto-approved
        owner_audit = AuditQueue(
            user_id=owner.id,
            submitted_payload={"source": "seed", "role": "owner"},
            status=AuditStatus.APPROVED.value,
        )
        db.add(owner_audit)

        # ── 2. Graduated members (demo alumni) ─────────────────────────────
        alumni = []
        for i in range(5):
            grad = User(
                email=f"alumni{i+1}@labinherit.local",
                password_hash=hash_password(f"Grad@{i+1}23"),
                display_name=f"已毕业师兄{i+1}",
                status=UserStatus.GRADUATED.value,
                role=UserRole.MEMBER.value,
                last_login_at=datetime.now(tz=timezone.utc),
            )
            db.add(grad)
            await db.flush()
            db.add(UserProfile(
                user_id=grad.id,
                enrollment_year=2019 + i,
                graduation_year=2023 + i,
                research_direction="深度学习",
                current_affiliation=f"某科技公司 {i+1}",
                bio=f"已毕业 {i+1} 年，偶尔回来看师弟们的问题。",
            ))
            db.add(AuditQueue(
                user_id=grad.id,
                submitted_payload={"source": "seed"},
                status=AuditStatus.APPROVED.value,
            ))
            alumni.append(grad)

        # ── 4. Active members (pending + approved) ─────────────────────────
        # Approved members
        for i in range(3):
            member = User(
                email=f"member{i+1}@labinherit.local",
                password_hash=hash_password(f"Member@{i+1}23"),
                display_name=f"在读师弟{i+1}",
                status=UserStatus.ACTIVE.value,
                role=UserRole.MEMBER.value,
            )
            db.add(member)
            await db.flush()
            db.add(UserProfile(
                user_id=member.id,
                enrollment_year=2024 - i,
                research_direction="计算机视觉",
            ))
            db.add(AuditQueue(
                user_id=member.id,
                submitted_payload={"source": "seed"},
                status=AuditStatus.APPROVED.value,
            ))

        # One pending member (for owner to approve)
        pending = User(
            email="pending@labinherit.local",
            password_hash=hash_password("Pending@123"),
            display_name="待审核新人",
            status=UserStatus.ACTIVE.value,
            role=UserRole.MEMBER.value,
        )
        db.add(pending)
        await db.flush()
        db.add(UserProfile(
            user_id=pending.id,
            enrollment_year=2025,
            research_direction="强化学习",
        ))
        db.add(AuditQueue(
            user_id=pending.id,
            submitted_payload={
                "source": "seed",
                "message": "我是新来的研究生，想学习项目经验！",
            },
            status=AuditStatus.PENDING.value,
        ))

        # ── 5. Invite codes ───────────────────────────────────────────────
        codes = []
        for i in range(3):
            code = secrets.token_urlsafe(9).upper().replace("-", "").replace("_", "")[:12]
            invite = Invite(
                code=code,
                created_by=owner.id,
                max_uses=1,
                note=f"第 {i+1} 个演示邀请码",
            )
            db.add(invite)
            codes.append(code)

        await db.commit()

        # ── Print summary ─────────────────────────────────────────────────
        print()
        print("✅  数据库已填充，以下账号均可登录：")
        print()
        print("【Owner（导师）】")
        print(f"  owner@labinherit.local  / Owner@123")
        print()
        print("【已毕业师兄师姐】")
        for i, g in enumerate(alumni):
            print(f"  alumni{i+1}@labinherit.local  / Grad@{i+1}23")
        print()
        print("【在读成员】")
        for i in range(3):
            print(f"  member{i+1}@labinherit.local  / Member@{i+1}23")
        print()
        print("【待审核】")
        print(f"  pending@labinherit.local  / Pending@123  ← 需导师批准后才能登录")
        print()
        print("【邀请码】")
        for c in codes:
            print(f"  {c}  (max_uses=1)")
        print()
        print("=" * 60)
        print("🔗  打开 http://localhost:5173 开始测试")
        print("📖  API 文档 http://localhost:8000/docs")
        print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(_seed())
