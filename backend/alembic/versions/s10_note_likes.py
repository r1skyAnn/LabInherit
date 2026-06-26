"""s10: note_likes table (prevent duplicate likes)

Revision ID: s10_note_likes
Revises: s9_showcase_experience
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s10_note_likes"
down_revision = "s9_showcase_experience"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "note_likes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("note_id", sa.BigInteger(), sa.ForeignKey("notes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("note_id", "user_id", name="uq_note_likes_note_user"),
    )
    op.create_index("ix_note_likes_note_id", "note_likes", ["note_id"])


def downgrade() -> None:
    op.drop_table("note_likes")
