"""Health-check endpoints.

GET /health                  — plain liveness probe
GET /api/v1/health           — liveness + DB ping
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Liveness probe")
async def health_root() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health-db", summary="Liveness + DB connectivity")
async def health_db(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "fail"
    return {"status": "ok", "db": db_status}
