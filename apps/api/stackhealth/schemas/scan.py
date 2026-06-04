"""Scan request and response schemas. See docs/09-API-DESIGN.md."""

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

GITHUB_URL_RE = re.compile(
    r"^https?://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.IGNORECASE
)


REF_RE = re.compile(r"^[\w./-]{1,255}$")


class ScanCreate(BaseModel):
    repo_url: str = Field(..., examples=["https://github.com/fastapi/fastapi"])
    # Required. Every scan needs a notification target so the user can
    # walk away from the polling page — most scans take 30s to several
    # minutes and we don't want to make people babysit a progress bar.
    notify_email: EmailStr
    # Optional branch or tag. If omitted, the repo's default branch is
    # cloned (the original v1 behaviour). Useful for scoring release
    # tags or feature branches.
    ref: str | None = Field(default=None, examples=["main", "v8.0.0"])

    @field_validator("repo_url")
    @classmethod
    def must_be_github_url(cls, v: str) -> str:
        if not GITHUB_URL_RE.match(v.strip()):
            raise ValueError("Must be a https://github.com/owner/repo URL")
        return v.strip()

    @field_validator("ref")
    @classmethod
    def ref_is_safe(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # git refs allow [A-Za-z0-9._/-] up to ~255 chars. Anything outside
        # that almost certainly contains a shell metacharacter — refuse
        # before it reaches the clone step.
        if not REF_RE.match(v):
            raise ValueError("ref may only contain letters, digits, dot, slash, dash, underscore")
        return v

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


class ScanNotifyUpdate(BaseModel):
    """Body for PATCH /api/scans/{id}/notify."""

    notify_email: EmailStr | None = Field(
        default=None,
        description="Set to an email to opt in, or null to opt out.",
    )


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
    default_branch: str | None = None
    pushed_at: datetime | None = None
    license_spdx: str | None = None


class ScanRead(BaseModel):
    id: uuid.UUID
    repo: RepoMini
    status: str
    formula_version: str
    requested_ref: str | None = None
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
    # `notify_enabled` is a boolean rather than echoing the email back, so the
    # scan endpoint stays privacy-safe (the scan_id is unguessable but the
    # endpoint is otherwise public).
    notify_enabled: bool = False
