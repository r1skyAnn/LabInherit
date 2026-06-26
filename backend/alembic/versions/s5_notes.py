"""s5: notes (Markdown notes with author snapshots)

Revision ID: s5_notes
Revises: s4_categories
Create Date: 2026-06-25

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s5_notes"
down_revision = "s4_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "category_id",
            sa.BigInteger(),
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "author_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("author_display_name", sa.String(64), nullable=False),
        sa.Column("author_email", sa.String(255), nullable=False),
        sa.Column("author_enrollment_year", sa.Integer(), nullable=True),
        sa.Column("author_graduation_year", sa.Integer(), nullable=True),
        sa.Column("is_pinned", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("like_count", sa.Integer(), server_default="0", nullable=False),
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
    op.create_index("ix_notes_project_category", "notes", ["project_id", "category_id"])
    op.create_index("ix_notes_author_id", "notes", ["author_id"])
    op.create_index("ix_notes_is_pinned", "notes", ["is_pinned"])
    op.create_index("ix_notes_project_id", "notes", ["project_id"])


def downgrade() -> None:
    op.drop_table("notes")
