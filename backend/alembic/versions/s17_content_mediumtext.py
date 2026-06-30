"""s17: enlarge guides.content & notes.content to MEDIUMTEXT

Revision ID: s17_content_mediumtext
Revises: s16_guide_attachments
Create Date: 2026-06-30

TEXT is capped at 65,535 bytes which a long Chinese-markdown note/guide
can easily exceed (UTF-8 Chinese = 3 bytes per char). MEDIUMTEXT supports
up to 16 MB.
"""

from __future__ import annotations

from alembic import op

revision = "s17_content_mediumtext"
down_revision = "s16_guide_attachments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE guides MODIFY COLUMN content MEDIUMTEXT NOT NULL")
    op.execute("ALTER TABLE notes MODIFY COLUMN content MEDIUMTEXT NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE guides MODIFY COLUMN content TEXT NOT NULL")
    op.execute("ALTER TABLE notes MODIFY COLUMN content TEXT NOT NULL")
