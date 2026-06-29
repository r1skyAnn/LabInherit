"""s15: files & note_attachments (unified attachment system)

Revision ID: s15_files_attachments
Revises: s14_alumni_posts_project_visibility
Create Date: 2026-06-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s15_files_attachments"
down_revision = "s14_alumni_posts_project_visibility"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "files",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("stored_name", sa.String(64), nullable=False),
        sa.Column("subdir", sa.String(32), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("category", sa.String(16), nullable=False, server_default="other"),
        sa.Column("is_deleted", sa.Boolean(), server_default="0", nullable=False),
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
    op.create_index("ix_files_owner_id", "files", ["owner_id"])
    op.create_index("ix_files_project_id", "files", ["project_id"])
    op.create_index("ix_files_owner_category", "files", ["owner_id", "category"])
    op.create_index("ix_files_subdir_stored", "files", ["subdir", "stored_name"])

    op.create_table(
        "note_attachments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "note_id",
            sa.BigInteger(),
            sa.ForeignKey("notes.id", ondelete="CASCADE"),
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
            nullable=False,
            server_default="attachment",
        ),
        sa.Column("position", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_note_attachments_note_id", "note_attachments", ["note_id"])
    op.create_index("ix_note_attachments_file_id", "note_attachments", ["file_id"])
    op.create_index("ix_note_attachments_note", "note_attachments", ["note_id"])


def downgrade() -> None:
    op.drop_table("note_attachments")
    op.drop_table("files")