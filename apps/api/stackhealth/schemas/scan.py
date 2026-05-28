"""Scan request and response schemas. See docs/09-API-DESIGN.md."""

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.IGNORECASE
)


class ScanCreate(BaseModel):
    repo_url: str = Field(..., examples=["https://github.com/fastapi/fastapi"])

    @field_validator("repo_url")
    @classmethod
    def must_be_github_url(cls, v: str) -> str:
        if not GITHUB_URL_RE.match(v.strip()):
            raise ValueError("Must be a https://github.com/owner/repo URL")
        return v.strip()

    @property
    def owner_and_name(self) -> tuple[str, str]:
        m = GITHUB_URL_RE.match(self.repo_url)
        assert m is not None
        return m.group(1), m.group(2)


class ScanCreateResponse(BaseModel):
    scan_id: uuid.UUID
    status: str
    polling_url: str
    report_url: str


class ScanScores(BaseModel):
    security: int
    quality: int
    hygiene: int
    community: int


class RepoMini(BaseModel):
    owner: str
    name: str
    stars: int | None = None
    language: str | None = None


class ScanRead(BaseModel):
    id: uuid.UUID
    repo: RepoMini
    status: str
    formula_version: str
    commit_sha: str | None = None
    overall_score: int | None = None
    grade: str | None = None
    scores: ScanScores | None = None
    score_breakdown: dict[str, Any] | None = None
    partial: bool = False
    failure_reason: str | None = None
    artifacts_url: str | None = None
    tool_versions: dict[str, str] | None = None
    created_at: datetime
    completed_at: datetime | None = None
