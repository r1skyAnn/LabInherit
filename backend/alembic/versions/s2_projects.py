"""s2: projects

Revision ID: s2_projects
Revises: s1_account_permissions
Create Date: 2026-06-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s2_projects"
down_revision = "s1_account_permissions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(16),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "priority",
            sa.String(16),
            server_default="medium",
            nullable=False,
        ),
        sa.Column("tech_stack", sa.String(512), nullable=True),
        sa.Column("repo_url", sa.String(512), nullable=True),
        sa.Column("demo_url", sa.String(512), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
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
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_projects_created_by", "projects", ["created_by"])

    op.create_check_constraint(
        "projects_status_valid", "projects",
        "status IN ('planning', 'active', 'paused', 'completed', 'abandoned')"
    )
    op.create_check_constraint(
        "projects_priority_valid", "projects",
        "priority IN ('low', 'medium', 'high')"
    )


def downgrade() -> None:
    op.drop_table("projects")
