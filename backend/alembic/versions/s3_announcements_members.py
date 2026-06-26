"""s3: announcements + members (no new tables, members is a read-only view via users)

Revision ID: s3_announcements_members
Revises: s2_projects
Create Date: 2026-06-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s3_announcements_members"
down_revision = "s2_projects"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "announcements",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "author_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("is_pinned", sa.Boolean(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_announcements_author_id", "announcements", ["author_id"])


def downgrade() -> None:
    op.drop_table("announcements")
