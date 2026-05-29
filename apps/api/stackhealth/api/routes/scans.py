"""POST /api/scans, GET /api/scans/:id, GET /api/scans/:id/findings.

Spec: docs/09-API-DESIGN.md
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from redis import Redis
from rq import Queue
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from stackhealth.api.deps import get_client_ip, get_db
from stackhealth.config import settings
from stackhealth.engines.github_meta import GitHubError, fetch_repo
from stackhealth.models import Repo, Scan, ScanFinding, ScanSubscriber
from stackhealth.models.scan import ScanStatus
from stackhealth.ratelimit import allow
from stackhealth.schemas import ScanCreate, ScanCreateResponse, ScanRead
from stackhealth.schemas.scan import RepoMini, ScanNotifyUpdate, ScanScores

router = APIRouter()
log = logging.getLogger(__name__)

QUEUE_NAME = "stackhealth"


@lru_cache
def _queue() -> Queue:
    conn = Redis.from_url(settings.redis_url)
    return Queue(QUEUE_NAME, connection=conn)


def _err(code: str, message: str, http: int) -> HTTPException:
    return HTTPException(status_code=http, detail={"error": {"code": code, "message": message}})


def _add_subscriber(db: Session, scan_id: uuid.UUID, email: str) -> None:
    """Idempotently subscribe `email` to `scan_id`. Duplicates are no-ops
    thanks to the (scan_id, email) composite primary key.
    """
    existing = db.scalar(
        select(ScanSubscriber).where(
            ScanSubscriber.scan_id == scan_id,
            ScanSubscriber.email == email,
        )
    )
    if existing is None:
        db.add(ScanSubscriber(scan_id=scan_id, email=email))


@router.post(
    "",
    response_model=ScanCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_scan(
    payload: ScanCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ScanCreateResponse:
    owner, name = payload.owner_and_name
    submitted_email = str(payload.notify_email)
    ip = get_client_ip(request)

    # 1. Rate limit by IP.
    if ip and not allow(
        f"ip:{ip}",
        limit=settings.rate_limit_scans_per_ip_per_hour,
        window_seconds=3600,
    ):
        raise _err("rate_limited", "Rate limit exceeded. Try again later.", 429)

    # 2. Per-repo dedupe (at most one scan per repo per hour).
    #
    # Three cases when an existing recent scan is found:
    #   • In progress (queued/cloning/analyzing/scoring):
    #       Add the submitter as another subscriber; return the existing
    #       scan_id. The worker emails everyone on completion.
    #   • Complete:
    #       The user is about to be redirected to the report. They
    #       don't need an email about something they're already
    #       looking at, so we DON'T add a subscription. Return the
    #       scan_id; the polling page hops them to the report.
    #   • Failed:
    #       Treat as if no scan exists — fall through to creating a
    #       fresh one.
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    if repo is not None:
        recent = db.scalar(
            select(Scan)
            .where(
                Scan.repo_id == repo.id,
                Scan.created_at >= datetime.now(UTC) - timedelta(hours=1),
            )
            .order_by(desc(Scan.created_at))
            .limit(1)
        )
        if recent is not None and recent.status != ScanStatus.failed:
            if recent.status != ScanStatus.complete:
                _add_subscriber(db, recent.id, submitted_email)
                db.commit()
            return ScanCreateResponse(
                scan_id=recent.id,
                status=recent.status.value,
                polling_url=f"/api/scans/{recent.id}",
                report_url=f"/r/{owner}/{name}/{recent.id}",
            )

    # 3. Confirm repo is public and exists.
    try:
        meta = fetch_repo(owner, name)
    except GitHubError as e:
        code = str(e)
        if code == "repo_not_found":
            raise _err("repo_not_found", "Repo not found or private.", 404) from e
        if code == "rate_limited":
            raise _err("github_rate_limited", "Upstream GitHub rate limit hit.", 503) from e
        raise _err("github_error", code, 502) from e
    if meta.is_private:
        raise _err("repo_private", "Private repos are not supported in MVP.", 404)

    # 4. Upsert repo with latest GitHub metadata.
    if repo is None:
        repo = Repo(owner=owner, name=name)
        db.add(repo)
    repo.description = meta.description
    repo.homepage = meta.homepage
    repo.default_branch = meta.default_branch
    repo.language = meta.language
    repo.stars = meta.stars
    repo.forks = meta.forks
    repo.license_spdx = meta.license_spdx
    repo.is_archived = meta.is_archived
    repo.is_fork = meta.is_fork
    repo.pushed_at = meta.pushed_at
    repo.updated_at = datetime.now(UTC)
    db.flush()

    # 5. Create scan row + first subscriber.
    scan = Scan(
        repo_id=repo.id,
        status=ScanStatus.queued,
        formula_version=settings.formula_version,
        requested_by_ip=ip,
        notify_email=submitted_email,  # deprecated; kept for back-compat
    )
    db.add(scan)
    db.flush()  # populate scan.id without commit
    _add_subscriber(db, scan.id, submitted_email)
    db.commit()
    db.refresh(scan)

    # 6. Enqueue worker job. Failure to enqueue doesn't fail the request;
    #    the row stays in `queued` until a worker is available.
    try:
        _queue().enqueue(
            "stackhealth.worker.jobs.run_scan",
            str(scan.id),
            job_timeout=settings.scan_wall_clock_timeout_seconds + 60,
            result_ttl=86400,
        )
    except Exception:
        log.exception("failed to enqueue scan %s", scan.id)

    return ScanCreateResponse(
        scan_id=scan.id,
        status=scan.status.value,
        polling_url=f"/api/scans/{scan.id}",
        report_url=f"/r/{owner}/{name}/{scan.id}",
    )


def _scan_to_read(scan: Scan, repo: Repo) -> ScanRead:
    scores = None
    if scan.security_score is not None:
        scores = ScanScores(
            security=scan.security_score or 0,
            quality=scan.quality_score or 0,
            hygiene=scan.hygiene_score or 0,
            community=scan.community_score or 0,
        )
    return ScanRead(
        id=scan.id,
        repo=RepoMini(
            owner=repo.owner,
            name=repo.name,
            stars=repo.stars,
            language=repo.language,
            default_branch=repo.default_branch,
            pushed_at=repo.pushed_at,
            license_spdx=repo.license_spdx,
        ),
        status=scan.status.value,
        formula_version=scan.formula_version,
        commit_sha=scan.commit_sha,
        overall_score=scan.overall_score,
        grade=scan.grade.value if scan.grade else None,
        scores=scores,
        score_breakdown=scan.score_breakdown,
        partial=scan.partial,
        failure_reason=scan.failure_reason,
        artifacts_url=scan.artifacts_url,
        tool_versions=scan.tool_versions,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        notify_enabled=bool(scan.notify_email),
    )


@router.patch("/{scan_id}/notify", status_code=204)
def set_notify_email(
    scan_id: uuid.UUID,
    payload: ScanNotifyUpdate,
    db: Session = Depends(get_db),
) -> None:
    """Add (or clear) a notification email for an in-progress scan.

    Once the scan is complete, the email would never fire — so we reject
    updates after the fact instead of silently ignoring them.
    """
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise _err("scan_not_found", "Scan not found.", 404)
    if scan.status == ScanStatus.complete:
        raise _err(
            "scan_already_complete",
            "Scan is already complete — no notification will fire.",
            409,
        )
    if scan.status == ScanStatus.failed:
        raise _err("scan_failed", "Scan failed — cannot subscribe to notify.", 409)
    scan.notify_email = str(payload.notify_email) if payload.notify_email else None
    db.commit()


@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id: uuid.UUID, db: Session = Depends(get_db)) -> ScanRead:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise _err("scan_not_found", "Scan not found.", 404)
    repo = db.get(Repo, scan.repo_id)
    assert repo is not None
    return _scan_to_read(scan, repo)


_SEV_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


@router.get("/{scan_id}/findings")
def get_findings(
    scan_id: uuid.UUID,
    engine: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise _err("scan_not_found", "Scan not found.", 404)

    stmt = select(ScanFinding).where(ScanFinding.scan_id == scan_id)
    if engine:
        stmt = stmt.where(ScanFinding.engine == engine)
    if severity:
        stmt = stmt.where(ScanFinding.severity == severity)
    rows = list(db.scalars(stmt).all())
    rows.sort(key=lambda r: _SEV_RANK.get(r.severity.value, 9))
    page = rows[offset : offset + limit]

    return {
        "findings": [
            {
                "id": str(f.id),
                "engine": f.engine.value,
                "severity": f.severity.value,
                "rule_id": f.rule_id,
                "title": f.title,
                "message": f.message,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "code_snippet": f.code_snippet,
            }
            for f in page
        ],
        "total": len(rows),
        "next_offset": offset + limit if offset + limit < len(rows) else None,
    }
