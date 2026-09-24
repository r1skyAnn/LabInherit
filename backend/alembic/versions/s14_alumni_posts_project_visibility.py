"""s14: alumni_posts + project visibility (is_public, project_viewers)

Revision ID: s14_alumni_posts_project_visibility
Revises: s13_user_gender
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s14_alumni_posts_project_visibility"
down_revision = "s13_user_gender"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Alumni posts table
    op.create_table(
        "alumni_posts",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("author_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("type", sa.String(16), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("company", sa.String(128), nullable=True),
        sa.Column("position", sa.String(128), nullable=True),
        sa.Column("contact_info", sa.String(256), nullable=True),
        sa.Column("tags", sa.String(256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_alumni_posts_type", "alumni_posts", ["type"])
    op.create_index("ix_alumni_posts_created_at", "alumni_posts", ["created_at"])

    # 2. Add is_public to projects
    op.add_column("projects", sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("1")))

    # 3. Project viewers table
    op.create_table(
        "project_viewers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.BigInteger(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    )
    op.create_index("ix_project_viewers_unique", "project_viewers", ["project_id", "user_id"], unique=True)


def downgrade() -> None:
    op.drop_table("project_viewers")
    op.drop_column("projects", "is_public")
    op.drop_table("alumni_posts")
