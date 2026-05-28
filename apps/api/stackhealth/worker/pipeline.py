"""End-to-end scan pipeline used by `worker.jobs.run_scan`.

Designed to be tolerant: each engine is optional. If a binary is missing or an
engine raises, the scan continues and `partial=True` is set on the result.
"""
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stackhealth.config import settings
from stackhealth.engines import (
    clone,
    cloc,
    community,
    complexity,
    duplication,
    github_meta,
    hygiene,
    lint,
    scorecard,
    semgrep,
    test_signal,
    trivy,
)
from stackhealth.engines._tools import tool_version
from stackhealth.formula.v1 import (
    FORMULA_VERSION,
    LetterGrade,
    community_score,
    overall as overall_score,
    quality_score,
    security_score,
)

log = logging.getLogger(__name__)


@dataclass
class EngineFailure:
    engine: str
    reason: str


@dataclass
class PipelineFindings:
    """Findings to persist into scan_findings table."""
    engine: str
    severity: str
    rule_id: str | None
    title: str
    message: str | None
    file_path: str | None
    line_number: int | None


@dataclass
class PipelineResult:
    security: int
    quality: int
    hygiene: int
    community: int
    overall: int
    grade: LetterGrade
    breakdown: dict[str, Any]
    findings: list[PipelineFindings] = field(default_factory=list)
    failures: list[EngineFailure] = field(default_factory=list)
    tool_versions: dict[str, str] = field(default_factory=dict)
    commit_sha: str | None = None
    artifacts_url: str | None = None
    partial: bool = False


def _safe(engine_name: str, fn, failures: list[EngineFailure], default=None):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        log.warning("engine %s failed: %s", engine_name, e)
        failures.append(EngineFailure(engine=engine_name, reason=f"{type(e).__name__}: {e}"))
        return default


def _persist_artifact(scan_id: str, kind: str, payload: Any) -> str | None:
    """Save raw engine output locally (R2 used in prod)."""
    base = os.environ.get("LOCAL_ARTIFACT_DIR")
    if not base:
        return None
    out = Path(base) / scan_id
    out.mkdir(parents=True, exist_ok=True)
    fn = out / f"{kind}.json"
    fn.write_text(json.dumps(payload, default=str))
    return str(fn)


def run(scan_id: str, owner: str, name: str) -> PipelineResult:
    """Execute the full pipeline. Caller wraps in a DB session to persist."""
    failures: list[EngineFailure] = []
    findings: list[PipelineFindings] = []
    breakdown: dict[str, Any] = {}
    tool_vers: dict[str, str] = {}

    # 1. Refresh GitHub metadata.
    meta = github_meta.fetch_repo(owner, name)
    breakdown["stars"] = meta.stars

    # 2. Clone.
    with clone.shallow_clone(meta.clone_url) as (commit_sha, workdir):
        log.info("cloned %s @ %s", f"{owner}/{name}", commit_sha)

        # 3. Cloc — needed for LoC normalisation everywhere.
        cloc_result = _safe("cloc", lambda: cloc.run(workdir), failures, default=None)
        loc = cloc_result.total_loc if cloc_result else 0
        languages = list(cloc_result.by_language) if cloc_result else []
        breakdown["loc"] = loc
        breakdown["languages"] = languages[:10]
        if cloc_result:
            _persist_artifact(scan_id, "cloc", cloc_result.raw)
            tool_vers["cloc"] = tool_version("cloc") or "unknown"

        # 4. Hygiene (always runs — pure filesystem).
        days_since = (
            (datetime.now(UTC) - meta.pushed_at).days if meta.pushed_at else None
        )
        hyg = hygiene.evaluate(
            workdir,
            license_spdx=meta.license_spdx,
            has_description=bool(meta.description),
            has_topics=bool(meta.topics),
            days_since_last_commit=days_since,
        )
        hyg_score = hyg.score
        breakdown["hygiene_breakdown"] = hyg.breakdown
        for k, points in hyg.breakdown.items():
            if points == 0:
                findings.append(
                    PipelineFindings(
                        engine="hygiene",
                        severity="info",
                        rule_id=f"hygiene.{k}",
                        title=f"Missing hygiene check: {k}",
                        message=None,
                        file_path=None,
                        line_number=None,
                    )
                )

        # 5. Test signal.
        ts = _safe(
            "test_signal", lambda: test_signal.run(workdir), failures,
            default=test_signal.TestSignalResult(score=0, breakdown={}),
        )
        breakdown["test_signal_breakdown"] = ts.breakdown

        # 6. File size derived from cloc.
        file_size_s = cloc.file_size_score(cloc_result.mega_files) if cloc_result else 50
        if cloc_result:
            breakdown["mega_files"] = cloc_result.mega_files

        # 7. Semgrep.
        sg = _safe("semgrep", lambda: semgrep.run(workdir), failures, default=None)
        if sg is not None:
            sem_score = semgrep.semgrep_score(
                errors=sg.errors, warnings=sg.warnings, info=sg.info, loc=loc
            )
            for f in sg.findings[:300]:
                sev_map = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
                findings.append(
                    PipelineFindings(
                        engine="semgrep",
                        severity=sev_map.get(f.severity, "low"),
                        rule_id=f.rule_id,
                        title=f"Semgrep: {f.rule_id}",
                        message=f.message,
                        file_path=f.file_path,
                        line_number=f.line,
                    )
                )
            _persist_artifact(scan_id, "semgrep", sg.raw)
            tool_vers["semgrep"] = tool_version("semgrep") or "unknown"
        else:
            sem_score = 75  # neutral default

        # 8. Trivy.
        tv = _safe("trivy", lambda: trivy.run(workdir), failures, default=None)
        if tv is not None:
            dep_score = trivy.dependency_score(
                critical=tv.critical, high=tv.high, medium=tv.medium, low=tv.low
            )
            for f in tv.findings[:300]:
                sev = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}.get(
                    f.severity, "low"
                )
                findings.append(
                    PipelineFindings(
                        engine="trivy",
                        severity=sev,
                        rule_id=f.vulnerability_id,
                        title=f"{f.vulnerability_id} in {f.package}",
                        message=f.title,
                        file_path=f.file_path,
                        line_number=None,
                    )
                )
            _persist_artifact(scan_id, "trivy", tv.raw)
            tool_vers["trivy"] = tool_version("trivy") or "unknown"
        else:
            dep_score = 80

        # 9. Complexity.
        cx = _safe("complexity", lambda: complexity.run(workdir), failures, default=None)
        if cx is not None:
            cx_score = complexity.complexity_score(cx.avg_complexity)
            breakdown["avg_complexity"] = round(cx.avg_complexity, 2)
            tool_vers["lizard"] = tool_version("lizard") or "unknown"
        else:
            cx_score = 75

        # 10. Duplication.
        dup = _safe("duplication", lambda: duplication.run(workdir), failures, default=None)
        if dup is not None:
            dup_score = duplication.duplication_score(dup.duplication_percent)
            breakdown["duplication_percent"] = round(dup.duplication_percent, 2)
            tool_vers["jscpd"] = tool_version("jscpd") or "unknown"
        else:
            dup_score = 85

        # 11. Lint.
        lt = _safe("lint", lambda: lint.run(workdir, languages), failures, default=None)
        if lt is not None and lt.total_issues >= 0 and (lt.by_language or loc > 0):
            lint_score = lint.lint_density_score(total_issues=lt.total_issues, loc=loc)
            breakdown["lint_issues"] = lt.total_issues
        else:
            lint_score = 80

    # workdir cleaned up — clone context exited.

    # 12. Scorecard (off-tree, runs after clone is fine).
    sc = _safe("scorecard", lambda: scorecard.fetch_or_run(owner, name), failures, default=None)
    if sc is not None:
        sc_aggregate = sc.aggregate
        _persist_artifact(scan_id, "scorecard", sc.raw)
        tool_vers["scorecard"] = "5.x"
    else:
        sc_aggregate = 5.0  # neutral 50

    # 13. Community signals.
    com_sig = _safe(
        "community",
        lambda: community.collect(
            owner, name, stars=meta.stars, pushed_at=meta.pushed_at
        ),
        failures,
        default=community.CommunitySignals(stars=meta.stars),
    )
    act = community.activity_score(
        days_since_last_commit=com_sig.days_since_last_commit,
        commits_last_90d=com_sig.commits_last_90d,
    )
    cont = community.contributor_score(com_sig.contributors_last_365d)
    pop = community.popularity_score(com_sig.stars)
    resp = community.responsiveness_score(
        com_sig.median_first_response_hours, com_sig.issues_in_90d
    )

    # 14. Compose sub-scores.
    sec = security_score(
        scorecard_0_10=sc_aggregate,
        semgrep_0_100=sem_score,
        dependency_0_100=dep_score,
    )
    qual = quality_score(
        complexity=cx_score,
        lint_density=lint_score,
        duplication=dup_score,
        test_signal=ts.score,
        file_size=file_size_s,
    )
    comm = community_score(activity=act, contributors=cont, popularity=pop, responsiveness=resp)
    total, grade = overall_score(sec, qual, hyg_score, comm)

    breakdown.update({
        "scorecard": round(sc_aggregate * 10),
        "semgrep": sem_score,
        "dependencies": dep_score,
        "complexity": cx_score,
        "lint_density": lint_score,
        "duplication": dup_score,
        "test_signal": ts.score,
        "file_size": file_size_s,
        "activity": act,
        "contributors": cont,
        "popularity": pop,
        "responsiveness": resp,
    })

    tool_vers["formula"] = FORMULA_VERSION

    return PipelineResult(
        security=sec,
        quality=qual,
        hygiene=hyg_score,
        community=comm,
        overall=total,
        grade=grade,
        breakdown=breakdown,
        findings=findings[:1000],
        failures=failures,
        tool_versions=tool_vers,
        commit_sha=commit_sha,
        artifacts_url=(
            f"{os.environ.get('R2_PUBLIC_URL', '')}/{scan_id}/"
            if os.environ.get("LOCAL_ARTIFACT_DIR") or os.environ.get("R2_PUBLIC_URL")
            else None
        ),
        partial=bool(failures),
    )
