"""GET /api/health and GET /api/stats — public liveness + stats."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from stackhealth import __version__
from stackhealth.api.deps import get_db
from stackhealth.config import settings
from stackhealth.models import Repo, Scan

router = APIRouter()


@router.get("/api/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "version": __version__,
        "formula_version": settings.formula_version,
    }


@router.get("/api/stats")
def stats(db: Session = Depends(get_db)) -> dict[str, int | float | None]:
    total_repos = db.scalar(select(func.count()).select_from(Repo)) or 0
    total_scans = db.scalar(select(func.count()).select_from(Scan)) or 0
    median_score = db.scalar(
        select(func.percentile_cont(0.5).within_group(Scan.overall_score)).where(
            Scan.overall_score.is_not(None)
        )
    )
    return {
        "total_repos_scanned": total_repos,
        "total_scans": total_scans,
        "median_overall_score": int(median_score) if median_score is not None else None,
    }
