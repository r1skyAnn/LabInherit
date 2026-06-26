"""s7: add is_ask column to comments

Revision ID: s7_is_ask
Revises: s6_comments
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s7_is_ask"
down_revision = "s6_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "comments",
        sa.Column("is_ask", sa.Boolean(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("comments", "is_ask")
