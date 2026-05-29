"""Public discovery endpoints: recent scans, top scans (leaderboard).

These power the landing-page sidebar. Cached aggressively at the edge —
no per-user data, completely public.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import and_, desc, select
from sqlalchemy.orm import Session

from stackhealth.api.deps import get_db
from stackhealth.models import Repo, Scan
from stackhealth.models.scan import ScanStatus

router = APIRouter()

# CDN cache: 60 seconds at the edge so the sidebar stays snappy without
# hammering Postgres. The cached set is small (10 rows) so it costs nothing.
_CACHE_HEADERS = {"Cache-Control": "public, max-age=60, s-maxage=60"}


def _row(scan: Scan, repo: Repo) -> dict:
    return {
        "scan_id": str(scan.id),
        "owner": repo.owner,
        "name": repo.name,
        "grade": scan.grade.value if scan.grade else None,
        "overall_score": scan.overall_score,
        "language": repo.language,
        "stars": repo.stars,
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
    }


@router.get("/api/discover/recent")
def recent_scans(
    response: Response,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> dict:
    """Most-recent completed scans, newest first.

    We collapse duplicates by (owner, name) — the latest scan of each repo wins,
    so the sidebar doesn't show the same repo three times in a row when someone
    rapidly re-runs.
    """
    response.headers.update(_CACHE_HEADERS)

    # Pull more than we need, then dedupe by repo_id keeping the latest.
    stmt = (
        select(Scan, Repo)
        .join(Repo, Repo.id == Scan.repo_id)
        .where(Scan.status == ScanStatus.complete)
        .order_by(desc(Scan.completed_at))
        .limit(limit * 4)
    )
    seen: set = set()
    rows: list[dict] = []
    for scan, repo in db.execute(stmt).all():
        if repo.id in seen:
            continue
        seen.add(repo.id)
        rows.append(_row(scan, repo))
        if len(rows) >= limit:
            break
    return {"scans": rows, "as_of": datetime.utcnow().isoformat() + "Z"}


@router.get("/api/discover/top")
def top_scans(
    response: Response,
    limit: int = Query(default=10, ge=1, le=50),
    min_stars: int = Query(
        default=0,
        ge=0,
        description="Filter to repos with at least this many stars (anti-gaming).",
    ),
    language: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict:
    """Highest-scoring scans (the leaderboard).

    Like /recent we dedupe per repo so a project's older scan doesn't crowd
    out its newer (and possibly worse) one — we always show the latest scan
    per repo, ranked by score.
    """
    response.headers.update(_CACHE_HEADERS)

    conds = [Scan.status == ScanStatus.complete, Scan.overall_score.is_not(None)]
    if min_stars > 0:
        conds.append(Repo.stars >= min_stars)
    if language:
        conds.append(Repo.language == language)

    # Take all qualifying scans, dedupe to the most-recent per repo, then sort
    # by score. SQL-side window functions would be cleaner but this is small.
    stmt = (
        select(Scan, Repo)
        .join(Repo, Repo.id == Scan.repo_id)
        .where(and_(*conds))
        .order_by(desc(Scan.completed_at))
        .limit(limit * 8)
    )
    latest_per_repo: dict = {}
    for scan, repo in db.execute(stmt).all():
        if repo.id not in latest_per_repo:
            latest_per_repo[repo.id] = (scan, repo)

    ranked = sorted(
        latest_per_repo.values(),
        key=lambda sr: sr[0].overall_score or 0,
        reverse=True,
    )[:limit]

    return {"scans": [_row(s, r) for s, r in ranked]}
