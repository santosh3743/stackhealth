"""Scan model — one row per scan attempt."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from stackhealth.database import Base


class ScanStatus(str, enum.Enum):
    queued = "queued"
    cloning = "cloning"
    analyzing = "analyzing"
    scoring = "scoring"
    complete = "complete"
    failed = "failed"


class LetterGrade(str, enum.Enum):
    a_plus = "A+"
    a = "A"
    a_minus = "A-"
    b_plus = "B+"
    b = "B"
    b_minus = "B-"
    c_plus = "C+"
    c = "C"
    c_minus = "C-"
    d = "D"
    f = "F"


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repos.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ScanStatus] = mapped_column(
        Enum(
            ScanStatus,
            name="scan_status",
            values_callable=lambda e: [m.value for m in e],
        ),
        default=ScanStatus.queued,
        nullable=False,
    )
    formula_version: Mapped[str] = mapped_column(Text, nullable=False)
    commit_sha: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[LetterGrade | None] = mapped_column(
        Enum(
            LetterGrade,
            name="letter_grade",
            values_callable=lambda e: [m.value for m in e],
        )
    )
    security_score: Mapped[int | None] = mapped_column(Integer)
    quality_score: Mapped[int | None] = mapped_column(Integer)
    hygiene_score: Mapped[int | None] = mapped_column(Integer)
    community_score: Mapped[int | None] = mapped_column(Integer)
    score_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    partial: Mapped[bool] = mapped_column(Boolean, default=False)
    failure_reason: Mapped[str | None] = mapped_column(Text)
    artifacts_url: Mapped[str | None] = mapped_column(Text)
    tool_versions: Mapped[dict | None] = mapped_column(JSONB)
    requested_by_ip: Mapped[str | None] = mapped_column(INET)
    notify_email: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
