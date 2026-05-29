"""RQ job entrypoints.

The single public job is `run_scan(scan_id)`. The actual engine orchestration
lives in `worker.pipeline.run` — this module is just the persistence shim.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from stackhealth.database import SessionLocal
from stackhealth.models import Repo, Scan, ScanFinding, ScanSubscriber
from stackhealth.models.finding import FindingEngine, FindingSeverity
from stackhealth.models.scan import LetterGrade as ScanLetterGrade
from stackhealth.models.scan import ScanStatus
from stackhealth.notify import send_scan_complete
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

    _PHASE_MAP = {
        "cloning": ScanStatus.cloning,
        "analyzing": ScanStatus.analyzing,
        "scoring": ScanStatus.scoring,
    }

    def _on_phase(phase: str) -> None:
        target = _PHASE_MAP.get(phase)
        if target is None:
            return
        with SessionLocal() as db:
            s = db.scalar(select(Scan).where(Scan.id == scan_uuid))
            if s is not None and s.status != target:
                s.status = target
                db.commit()

    try:
        result = pipeline.run(str(scan_uuid), owner, name, on_phase=_on_phase)
    except Exception as exc:
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

    # Best-effort completion email for every subscriber. Worker retries
    # are safe because we only send to subscribers with notified_at IS
    # NULL, then mark them. A subscriber added AFTER completion (which
    # we don't currently support, but might in the future) would get
    # picked up on the next pass.
    scores = {
        "security": result.security,
        "quality": result.quality,
        "hygiene": result.hygiene,
        "community": result.community,
    }
    # Snapshot repo meta once for everyone in this batch.
    language = stars = None
    with SessionLocal() as db:
        r = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
        if r is not None:
            language = r.language
            stars = r.stars

    with SessionLocal() as db:
        pending = list(
            db.scalars(
                select(ScanSubscriber).where(
                    ScanSubscriber.scan_id == scan_uuid,
                    ScanSubscriber.notified_at.is_(None),
                )
            ).all()
        )

        for sub in pending:
            try:
                send_scan_complete(
                    to_email=sub.email,
                    owner=owner,
                    name=name,
                    scan_id=str(scan_uuid),
                    overall=result.overall,
                    grade=result.grade.value,
                    partial=result.partial,
                    scores=scores,
                    language=language,
                    stars=stars,
                )
                sub.notified_at = datetime.now(UTC)
            except Exception:
                log.exception("notify failed for scan %s subscriber %s", scan_uuid, sub.email)
                # Leave notified_at NULL so a retry picks it up later.

        db.commit()
        log.info(
            "scan %s notified %d/%d subscribers",
            scan_uuid,
            sum(1 for s in pending if s.notified_at is not None),
            len(pending),
        )
