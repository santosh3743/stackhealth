"""scan_subscribers — many emails per scan

Replaces the single `Scan.notify_email` column with a proper many-to-one
table. A single in-progress scan can now have multiple users subscribed
to its completion email, which happens whenever someone re-submits the
same repo before the first scan finishes.

Backfills any existing `Scan.notify_email` values into the new table so
in-flight scans still notify the original submitter.

`Scan.notify_email` is intentionally kept (deprecated) so the old code
path stays alive during a hot rebuild — it's removed in a follow-up
migration once we've verified the new path.

Revision ID: 003
Revises: 002
Create Date: 2026-05-29
"""

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | list[str] | None = None
depends_on: str | list[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_subscribers",
        sa.Column(
            "scan_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.Text, nullable=False),
        sa.Column(
            "subscribed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "notified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("scan_id", "email", name="pk_scan_subscribers"),
    )

    op.create_index(
        "idx_scan_subscribers_pending",
        "scan_subscribers",
        ["scan_id"],
        postgresql_where=sa.text("notified_at IS NULL"),
    )

    # Backfill: any scan with a notify_email becomes its own first subscriber.
    op.execute(
        """
        INSERT INTO scan_subscribers (scan_id, email)
        SELECT id, notify_email
        FROM scans
        WHERE notify_email IS NOT NULL
        ON CONFLICT DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("idx_scan_subscribers_pending", table_name="scan_subscribers")
    op.drop_table("scan_subscribers")
