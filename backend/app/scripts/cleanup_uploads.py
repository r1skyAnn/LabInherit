"""Cleanup script for soft-deleted files.

Removes physical files from disk when:
  1. `is_deleted=True` AND the row was updated more than `grace_days` ago

Also removes orphaned files (no matching DB record).

Usage:
    python -m app.scripts.cleanup_uploads [--grace-days 30] [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal

# Force-register all models on Base.metadata (matches alembic env.py).
# Order matters: modules with relationships must come after their dependencies.
from app.modules.audit.models import AuditQueue  # noqa: F401  (User references its table)
from app.modules.users.models import User  # noqa: F401
from app.modules.invites.models import Invite  # noqa: F401
from app.modules.projects.models import Project  # noqa: F401
from app.modules.announcements.models import Announcement  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.notes.models import Note  # noqa: F401
from app.modules.files.models import File, NoteAttachment  # noqa: F401


async def cleanup_soft_deleted(grace_days: int, dry_run: bool) -> tuple[int, int]:
    """Returns (rows_considered, rows_removed)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=grace_days)
    removed = 0
    considered = 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(File).where(
                File.is_deleted.is_(True),
                File.updated_at < cutoff,
            )
        )
        rows = list(result.scalars().all())
        considered = len(rows)
        print(f"[soft-deleted] {considered} files past {grace_days}-day grace")

        for f in rows:
            path = Path(settings.UPLOAD_DIR) / "files" / f.subdir / f.stored_name
            if path.exists():
                if dry_run:
                    print(f"  [dry-run] would remove {path}")
                else:
                    try:
                        os.remove(path)
                        print(f"  removed {path}")
                    except OSError as e:
                        print(f"  ERROR removing {path}: {e}", file=sys.stderr)
                        continue
            else:
                print(f"  already absent: {path}")
            if not dry_run:
                await db.delete(f)
                removed += 1

        if not dry_run:
            await db.commit()

    return considered, removed


async def cleanup_orphans(dry_run: bool) -> tuple[int, int]:
    """Remove files on disk that have no DB record (e.g. from interrupted uploads)."""
    base = Path(settings.UPLOAD_DIR) / "files"
    if not base.exists():
        return 0, 0

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(File.stored_name, File.subdir, File.is_deleted))
        known = {(s, sd) for s, sd, _ in result.all()}

    removed = 0
    considered = 0
    for p in base.rglob("*"):
        if not p.is_file() or p.name.startswith("."):
            continue
        subdir = p.parent.relative_to(base).as_posix()
        if (p.name, subdir) not in known:
            considered += 1
            if dry_run:
                print(f"  [dry-run] would remove orphan {p}")
            else:
                try:
                    os.remove(p)
                    print(f"  removed orphan {p}")
                    removed += 1
                except OSError as e:
                    print(f"  ERROR removing {p}: {e}", file=sys.stderr)

    print(f"[orphans] {considered} files past grace, {removed} removed")
    return considered, removed


async def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up old/orphaned uploaded files")
    parser.add_argument("--grace-days", type=int, default=30, help="Days to keep soft-deleted files before permanent removal")
    parser.add_argument("--include-orphans", action="store_true", help="Also remove orphaned files (no DB record)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed without doing it")
    args = parser.parse_args()

    print(f"=== Cleanup run at {datetime.now(timezone.utc).isoformat()} ===")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Grace days: {args.grace_days}")
    print(f"Include orphans: {args.include_orphans}")
    print()

    soft_considered, soft_removed = await cleanup_soft_deleted(args.grace_days, args.dry_run)
    orphan_considered = orphan_removed = 0
    if args.include_orphans:
        orphan_considered, orphan_removed = await cleanup_orphans(args.dry_run)

    print()
    print("=== Summary ===")
    print(f"  Soft-deleted files: {soft_considered} considered, {soft_removed} removed")
    if args.include_orphans:
        print(f"  Orphaned files:     {orphan_considered} found, {orphan_removed} removed")


if __name__ == "__main__":
    asyncio.run(main())