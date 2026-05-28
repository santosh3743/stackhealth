"""RQ job entrypoints.

The single public job is `run_scan(scan_id)`. The actual engine orchestration
lives in `worker.pipeline.run` — this module is just the persistence shim.
"""
import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from stackhealth.database import SessionLocal
from stackhealth.models import Repo, Scan, ScanFinding
from stackhealth.models.finding import FindingEngine, FindingSeverity
from stackhealth.models.scan import LetterGrade as ScanLetterGrade, ScanStatus
from stackhealth.worker import pipeline

log = logging.getLogger(__name__)

_GRADE_MAP = {
    "A+": ScanLetterGrade.a_plus,
    "A": ScanLetterGrade.a,
    "A-": ScanLetterGrade.a_minus,
    "B+": ScanLetterGrade.b_plus,
    "B": ScanLetterGrade.b,
    "B-": ScanLetterGrade.b_minus,
    "C+": ScanLetterGrade.c_plus,
    "C": ScanLetterGrade.c,
    "C-": ScanLetterGrade.c_minus,
    "D": ScanLetterGrade.d,
    "F": ScanLetterGrade.f,
}


def run_scan(scan_id: str | uuid.UUID) -> None:
    """Single entrypoint for a scan job. Idempotent on retry."""
    scan_uuid = uuid.UUID(str(scan_id))
    log.info("starting scan %s", scan_uuid)

    with SessionLocal() as db:
        scan = db.scalar(select(Scan).where(Scan.id == scan_uuid))
        if scan is None:
            log.error("scan %s not found", scan_uuid)
            return
        repo = db.get(Repo, scan.repo_id)
        if repo is None:
            log.error("repo for scan %s not found", scan_uuid)
            return
        owner, name = repo.owner, repo.name

        scan.status = ScanStatus.cloning
        db.commit()

    try:
        result = pipeline.run(str(scan_uuid), owner, name)
    except Exception as exc:  # noqa: BLE001
        log.exception("scan %s failed", scan_uuid)
        with SessionLocal() as db:
            s = db.scalar(select(Scan).where(Scan.id == scan_uuid))
            if s is not None:
                s.status = ScanStatus.failed
                s.failure_reason = f"{type(exc).__name__}: {str(exc)[:200]}"
                s.completed_at = datetime.now(UTC)
                db.commit()
        raise

    with SessionLocal() as db:
        s = db.scalar(select(Scan).where(Scan.id == scan_uuid))
        if s is None:
            return
        s.status = ScanStatus.complete
        s.completed_at = datetime.now(UTC)
        s.commit_sha = result.commit_sha
        s.overall_score = result.overall
        s.grade = _GRADE_MAP[result.grade.value]
        s.security_score = result.security
        s.quality_score = result.quality
        s.hygiene_score = result.hygiene
        s.community_score = result.community
        s.score_breakdown = result.breakdown
        s.tool_versions = result.tool_versions
        s.artifacts_url = result.artifacts_url
        s.partial = result.partial
        if result.failures:
            s.failure_reason = "; ".join(f.engine for f in result.failures)

        db.query(ScanFinding).filter(ScanFinding.scan_id == scan_uuid).delete()
        for f in result.findings:
            try:
                engine_enum = FindingEngine(f.engine)
                sev_enum = FindingSeverity(f.severity)
            except ValueError:
                continue
            db.add(
                ScanFinding(
                    scan_id=scan_uuid,
                    engine=engine_enum,
                    severity=sev_enum,
                    rule_id=f.rule_id,
                    title=f.title,
                    message=f.message,
                    file_path=f.file_path,
                    line_number=f.line_number,
                )
            )
        db.commit()

    log.info("scan %s complete: %s (%s)", scan_uuid, result.overall, result.grade.value)
