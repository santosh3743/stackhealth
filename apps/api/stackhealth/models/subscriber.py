"""ScanSubscriber model — one row per (scan_id, email).

Replaces the single-string `Scan.notify_email`. Multiple users can subscribe
to a scan's completion notification by submitting the same repo while a
scan is in flight.

`notified_at` is null until the worker actually fires the email — that
lets us be idempotent if the worker is retried, and lets us audit who
got notified when.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, PrimaryKeyConstraint, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from stackhealth.database import Base


class ScanSubscriber(Base):
    __tablename__ = "scan_subscribers"
    __table_args__ = (PrimaryKeyConstraint("scan_id", "email", name="pk_scan_subscribers"),)

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    subscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
