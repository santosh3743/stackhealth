"""FormulaVersion model — registry of published formula versions."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from stackhealth.database import Base


class FormulaVersion(Base):
    __tablename__ = "formula_versions"

    version: Mapped[str] = mapped_column(Text, primary_key=True)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    spec_url: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
