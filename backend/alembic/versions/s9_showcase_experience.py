"""s9: add experience column to showcase_items

Revision ID: s9_showcase_experience
Revises: s8_showcase
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s9_showcase_experience"
down_revision = "s8_showcase"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "showcase_items",
        sa.Column("experience", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("showcase_items", "experience")
