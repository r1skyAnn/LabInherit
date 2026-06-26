"""s13: add gender to user_profiles

Revision ID: s13_user_gender
Revises: s12_guides
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s13_user_gender"
down_revision = "s12_guides"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_profiles",
        sa.Column("gender", sa.String(8), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "gender")
