"""GET /api/repos/:owner/:name and /latest."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from stackhealth.api.deps import get_db
from stackhealth.models import Repo, Scan
from stackhealth.models.scan import ScanStatus

router = APIRouter()


def _scan_summary(scan: Scan) -> dict:
    return {
        "id": str(scan.id),
        "grade": scan.grade.value if scan.grade else None,
        "overall_score": scan.overall_score,
        "security_score": scan.security_score,
        "quality_score": scan.quality_score,
        "hygiene_score": scan.hygiene_score,
        "community_score": scan.community_score,
        "commit_sha": scan.commit_sha,
        "completed_at": scan.completed_at,
    }


@router.get("/{owner}/{name}")
def get_repo(owner: str, name: str, db: Session = Depends(get_db)) -> dict:
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    if repo is None:
        raise HTTPException(status_code=404, detail="repo not yet scanned")

    complete_scans = list(
        db.scalars(
            select(Scan)
            .where(Scan.repo_id == repo.id, Scan.status == ScanStatus.complete)
            .order_by(desc(Scan.completed_at))
            .limit(20)
        ).all()
    )

    return {
        "owner": repo.owner,
        "name": repo.name,
        "stars": repo.stars,
        "forks": repo.forks,
        "language": repo.language,
        "license_spdx": repo.license_spdx,
        "is_archived": repo.is_archived,
        "is_fork": repo.is_fork,
        "first_seen_at": repo.first_seen_at,
        "latest_scan": _scan_summary(complete_scans[0]) if complete_scans else None,
        "scan_history": [_scan_summary(s) for s in complete_scans],
    }


@router.get("/{owner}/{name}/recent")
def get_recent_scan(owner: str, name: str, db: Session = Depends(get_db)) -> dict:
    """Most recent scan of any status (queued / running / complete / failed).

    Lets the frontend's not-yet-scanned page distinguish "we're already
    scanning, want to subscribe?" from "let's start a new scan".
    """
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    if repo is None:
        raise HTTPException(status_code=404, detail="repo not yet seen")
    scan = db.scalar(
        select(Scan).where(Scan.repo_id == repo.id).order_by(desc(Scan.created_at)).limit(1)
    )
    if scan is None:
        raise HTTPException(status_code=404, detail="no scans yet")
    return {
        "id": str(scan.id),
        "status": scan.status.value,
        "grade": scan.grade.value if scan.grade else None,
        "overall_score": scan.overall_score,
        "created_at": scan.created_at,
        "completed_at": scan.completed_at,
    }


@router.get("/{owner}/{name}/latest")
def get_latest_scan(owner: str, name: str, db: Session = Depends(get_db)) -> dict:
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    if repo is None:
        raise HTTPException(status_code=404, detail="repo not yet scanned")

    scan = db.scalar(
        select(Scan)
        .where(Scan.repo_id == repo.id, Scan.status == ScanStatus.complete)
        .order_by(desc(Scan.completed_at))
        .limit(1)
    )
    if scan is None:
        raise HTTPException(status_code=404, detail="no complete scan yet")
    return {
        "id": str(scan.id),
        "owner": owner,
        "name": name,
        "overall_score": scan.overall_score,
        "grade": scan.grade.value if scan.grade else None,
        "completed_at": scan.completed_at,
    }
