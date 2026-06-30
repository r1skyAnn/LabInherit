"""Alembic environment — async-aware.

Reads the database URL from app.core.config so we keep secrets out of
alembic.ini. Detects whether the migration should run online (real DB) or
offline (generate SQL).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import settings and Base so autogenerate sees our models
from app.core.config import settings
from app.db import Base  # noqa: F401  (registers metadata)

# Import all models so their tables register on Base.metadata
# S1: account & permissions
from app.modules.users.models import User, UserProfile  # noqa: F401
from app.modules.invites.models import Invite  # noqa: F401
from app.modules.audit.models import AuditQueue  # noqa: F401
from app.modules.projects.models import Project  # noqa: F401
from app.modules.announcements.models import Announcement  # noqa: F401
from app.modules.categories.models import Category  # noqa: F401
from app.modules.notes.models import Note  # noqa: F401
from app.modules.files.models import File, NoteAttachment  # noqa: F401
from app.modules.guides.models import Guide, GuideAttachment  # noqa: F401

config = context.config

# Inject the URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emits SQL to stdout/file."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with an async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
