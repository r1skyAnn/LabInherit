"""s11: categories become global, projects get category_id + zip_url

Revision ID: s11_global_categories
Revises: s10_note_likes
Create Date: 2026-06-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "s11_global_categories"
down_revision = "s10_note_likes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Categories: drop project_id FK (find actual name) + indexes + column
    conn = op.get_bind()
    fks = conn.execute(
        sa.text(
            "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'categories' "
            "AND COLUMN_NAME = 'project_id' AND REFERENCED_TABLE_NAME IS NOT NULL"
        )
    ).fetchall()
    for row in fks:
        op.drop_constraint(row[0], "categories", type_="foreignkey")

    # Drop any index on project_id
    idxs = conn.execute(
        sa.text(
            "SHOW INDEX FROM categories WHERE Column_name = 'project_id'"
        )
    ).fetchall()
    dropped = set()
    for row in idxs:
        name = row[2]  # Key_name column
        if name not in dropped:
            dropped.add(name)
            op.drop_index(name, table_name="categories")

    op.drop_column("categories", "project_id")

    # Projects: add category_id + zip_url
    op.add_column("projects", sa.Column("category_id", sa.BigInteger(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True))
    op.add_column("projects", sa.Column("zip_url", sa.String(512), nullable=True))
    op.create_index("ix_projects_category_id", "projects", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_projects_category_id", table_name="projects")
    op.drop_column("projects", "zip_url")
    op.drop_column("projects", "category_id")

    op.add_column("categories", sa.Column("project_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_categories_project_id", "categories", ["project_id"])
    op.create_foreign_key("fk_categories_project_id_projects", "categories", "projects", ["project_id"], ["id"], ondelete="CASCADE")
