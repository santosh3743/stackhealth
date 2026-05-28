"""Repo model — one row per unique repository ever scanned."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from stackhealth.database import Base


class Repo(Base):
    __tablename__ = "repos"
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_repos_owner_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    homepage: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    stars: Mapped[int | None] = mapped_column(Integer)
    forks: Mapped[int | None] = mapped_column(Integer)
    license_spdx: Mapped[str | None] = mapped_column(Text)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_fork: Mapped[bool] = mapped_column(Boolean, default=False)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"
