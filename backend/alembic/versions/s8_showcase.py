"""s8: showcase (成果展示 + 寄语墙)

Revision ID: s8_showcase
Revises: s7_is_ask
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s8_showcase"
down_revision = "s7_is_ask"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "showcase_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "author_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("type", sa.String(16), nullable=False),  # achievement / blessing
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_url", sa.String(512), nullable=True),
        sa.Column("pdf_url", sa.String(512), nullable=True),
        sa.Column("contact_info", sa.String(256), nullable=True),  # blessing contact
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_showcase_type", "showcase_items", ["type"])
    op.create_index("ix_showcase_author_id", "showcase_items", ["author_id"])


def downgrade() -> None:
    op.drop_table("showcase_items")
