"""add requested_ref to scans

Lets the API target a specific branch or tag (e.g. v2-beta, release/8.x)
instead of always cloning the repo's default branch. The column is
nullable — NULL means "scan the default branch", matching prior behavior
for every existing row.

Revision ID: 004
Revises: 003
Create Date: 2026-06-04
"""

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("requested_ref", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("scans", "requested_ref")
