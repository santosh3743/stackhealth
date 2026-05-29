"""add notify_email to scans

Revision ID: 002
Revises: 001
Create Date: 2026-05-29
"""

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("notify_email", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scans", "notify_email")
