"""s16: guide_attachments — link File records to Guide entries

Revision ID: s16_guide_attachments
Revises: s15_files_attachments
Create Date: 2026-06-30

Mirrors the note_attachments pattern so guides can attach arbitrary
uploaded files just like notes do.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s16_guide_attachments"
down_revision = "s15_files_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guide_attachments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "guide_id",
            sa.BigInteger(),
            sa.ForeignKey("guides.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "file_id",
            sa.BigInteger(),
            sa.ForeignKey("files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(16),
            server_default="attachment",
            nullable=False,
        ),
        sa.Column(
            "position",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_guide_attachments_guide", "guide_attachments", ["guide_id"]
    )
    op.create_index(
        "ix_guide_attachments_file", "guide_attachments", ["file_id"]
    )


def downgrade() -> None:
    op.drop_table("guide_attachments")
