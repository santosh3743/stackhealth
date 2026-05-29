"""End-to-end scan pipeline used by `worker.jobs.run_scan`.

Designed to be tolerant: each engine is optional. If a binary is missing or
an engine raises, the scan continues and `partial=True` is set on the
result. Missing values are substituted with the documented neutral
defaults in `stackhealth.formula.defaults`.

The orchestration in `run()` is split into three phases:

    cloning   → fetch GitHub meta + shallow clone
    analyzing → all in-workdir engines (hygiene, cloc, semgrep, trivy, …)
    scoring   → off-workdir engines (scorecard, community) + formula

Each phase emits an `on_phase(name)` callback so the polling UI can show
real progress.
"""

import json
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from stackhealth.engines import (
    cloc,
    clone,
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
from stackhealth.engines._registry import detect_versions
from stackhealth.formula.defaults import (
    NEUTRAL_COMPLEXITY_SCORE,
    NEUTRAL_DEPENDENCY_SCORE,
    NEUTRAL_DUPLICATION_SCORE,
    NEUTRAL_FILE_SIZE_SCORE,
    NEUTRAL_LINT_SCORE,
    NEUTRAL_SCORECARD_AGGREGATE,
    NEUTRAL_SEMGREP_SCORE,
)
from stackhealth.formula.v1 import (
    FORMULA_VERSION,
    LetterGrade,
    community_score,
    quality_score,
    security_score,
)
from stackhealth.formula.v1 import overall as overall_score

log = logging.getLogger(__name__)

# Cap findings persisted per engine — the rest stay in the R2 raw artifact.
_FINDINGS_CAP_PER_ENGINE = 300
# Total findings cap to keep the report page snappy.
_FINDINGS_CAP_TOTAL = 1000

# Severity translation tables — engine-specific labels → our enum.
_SEMGREP_SEVERITY = {"ERROR": "high", "WARNING": "medium", "INFO": "low"}
_TRIVY_SEVERITY = {"CRITICAL": "critical", "HIGH": "high", "MEDIUM": "medium", "LOW": "low"}


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


# ─────────────────────────────────────────────────────────────────────
# helpers


def _safe(engine_name: str, fn, failures: list[EngineFailure], default=None):
    """Call `fn()`, append to failures on exception, return default on failure."""
    try:
        return fn()
    except Exception as e:
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


def _hygiene_findings(breakdown: dict[str, int]) -> list[PipelineFindings]:
    """Each failing hygiene check becomes an info-level finding for visibility."""
    return [
        PipelineFindings(
            engine="hygiene",
            severity="info",
            rule_id=f"hygiene.{key}",
            title=f"Missing hygiene check: {key}",
            message=None,
            file_path=None,
            line_number=None,
        )
        for key, points in breakdown.items()
        if points == 0
    ]


def _semgrep_findings(result: semgrep.SemgrepResult) -> list[PipelineFindings]:
    return [
        PipelineFindings(
            engine="semgrep",
            severity=_SEMGREP_SEVERITY.get(f.severity, "low"),
            rule_id=f.rule_id,
            title=f"Semgrep: {f.rule_id}",
            message=f.message,
            file_path=f.file_path,
            line_number=f.line,
        )
        for f in result.findings[:_FINDINGS_CAP_PER_ENGINE]
    ]


def _trivy_findings(result: trivy.TrivyResult) -> list[PipelineFindings]:
    return [
        PipelineFindings(
            engine="trivy",
            severity=_TRIVY_SEVERITY.get(f.severity, "low"),
            rule_id=f.vulnerability_id,
            title=f"{f.vulnerability_id} in {f.package}",
            message=f.title,
            file_path=f.file_path,
            line_number=None,
        )
        for f in result.findings[:_FINDINGS_CAP_PER_ENGINE]
    ]


def _artifacts_url(scan_id: str) -> str | None:
    """Public URL prefix for raw scan artifacts, or None if storage is disabled."""
    if not (os.environ.get("LOCAL_ARTIFACT_DIR") or os.environ.get("R2_PUBLIC_URL")):
        return None
    return f"{os.environ.get('R2_PUBLIC_URL', '')}/{scan_id}/"


# ─────────────────────────────────────────────────────────────────────
# scoring (broken out so tests can target each dimension independently)


def _compute_security(
    sc_aggregate: float, sem_score: int, dep_score: int
) -> tuple[int, dict[str, int]]:
    """Returns (security_score, {scorecard, semgrep, dependencies} for breakdown)."""
    score = security_score(
        scorecard_0_10=sc_aggregate,
        semgrep_0_100=sem_score,
        dependency_0_100=dep_score,
    )
    return score, {
        "scorecard": round(sc_aggregate * 10),
        "semgrep": sem_score,
        "dependencies": dep_score,
    }


def _compute_quality(
    cx_score: int,
    lint_score: int,
    dup_score: int,
    ts_score: int,
    file_size_s: int,
) -> tuple[int, dict[str, int]]:
    score = quality_score(
        complexity=cx_score,
        lint_density=lint_score,
        duplication=dup_score,
        test_signal=ts_score,
        file_size=file_size_s,
    )
    return score, {
        "complexity": cx_score,
        "lint_density": lint_score,
        "duplication": dup_score,
        "test_signal": ts_score,
        "file_size": file_size_s,
    }


def _compute_community(sig: community.CommunitySignals) -> tuple[int, dict[str, int]]:
    act = community.activity_score(
        days_since_last_commit=sig.days_since_last_commit,
        commits_last_90d=sig.commits_last_90d,
    )
    cont = community.contributor_score(sig.contributors_last_365d)
    pop = community.popularity_score(sig.stars)
    resp = community.responsiveness_score(sig.median_first_response_hours, sig.issues_in_90d)
    score = community_score(activity=act, contributors=cont, popularity=pop, responsiveness=resp)
    return score, {
        "activity": act,
        "contributors": cont,
        "popularity": pop,
        "responsiveness": resp,
    }


# ─────────────────────────────────────────────────────────────────────
# main entry


def run(
    scan_id: str,
    owner: str,
    name: str,
    on_phase: Callable[[str], None] | None = None,
) -> PipelineResult:
    """Execute the full pipeline. Caller wraps in a DB session to persist."""

    def _phase(phase: str) -> None:
        if on_phase is not None:
            try:
                on_phase(phase)
            except Exception:
                log.exception("on_phase callback raised; continuing")

    failures: list[EngineFailure] = []
    findings: list[PipelineFindings] = []
    breakdown: dict[str, Any] = {}
    # Engines that successfully produced output. We use this at the end to
    # build `tool_versions` via the engine registry, instead of sprinkling
    # `tool_vers["x"] = tool_version("x") or "unknown"` calls throughout.
    succeeded: set[str] = set()

    # ── phase 1: cloning ──────────────────────────────────────────
    _phase("cloning")
    meta = github_meta.fetch_repo(owner, name)
    breakdown["stars"] = meta.stars

    with clone.shallow_clone(meta.clone_url) as (commit_sha, workdir):
        log.info("cloned %s @ %s", f"{owner}/{name}", commit_sha)
        _phase("analyzing")

        # ── phase 2a: cloc — feeds LoC normalisation everywhere ──
        cloc_result = _safe("cloc", lambda: cloc.run(workdir), failures)
        loc = cloc_result.total_loc if cloc_result else 0
        languages = list(cloc_result.by_language) if cloc_result else []
        breakdown["loc"] = loc
        breakdown["languages"] = languages[:10]
        if cloc_result:
            _persist_artifact(scan_id, "cloc", cloc_result.raw)
            succeeded.add("cloc")

        # ── phase 2b: hygiene (always — pure filesystem) ─────────
        days_since = (datetime.now(UTC) - meta.pushed_at).days if meta.pushed_at else None
        hyg = hygiene.evaluate(
            workdir,
            license_spdx=meta.license_spdx,
            has_description=bool(meta.description),
            has_topics=bool(meta.topics),
            days_since_last_commit=days_since,
        )
        hyg_score = hyg.score
        breakdown["hygiene_breakdown"] = hyg.breakdown
        findings.extend(_hygiene_findings(hyg.breakdown))

        # ── phase 2c: test signal — pure filesystem ──────────────
        ts = _safe(
            "test_signal",
            lambda: test_signal.run(workdir),
            failures,
            default=test_signal.TestSignalResult(score=0, breakdown={}),
        )
        breakdown["test_signal_breakdown"] = ts.breakdown

        # ── phase 2d: file size — derived from cloc ──────────────
        if cloc_result:
            file_size_s = cloc.file_size_score(cloc_result.mega_files)
            breakdown["mega_files"] = cloc_result.mega_files
        else:
            file_size_s = NEUTRAL_FILE_SIZE_SCORE

        # ── phase 2e: semgrep ────────────────────────────────────
        sg = _safe("semgrep", lambda: semgrep.run(workdir), failures)
        if sg is not None:
            sem_score = semgrep.semgrep_score(
                errors=sg.errors, warnings=sg.warnings, info=sg.info, loc=loc
            )
            findings.extend(_semgrep_findings(sg))
            _persist_artifact(scan_id, "semgrep", sg.raw)
            succeeded.add("semgrep")
        else:
            sem_score = NEUTRAL_SEMGREP_SCORE

        # ── phase 2f: trivy ──────────────────────────────────────
        tv = _safe("trivy", lambda: trivy.run(workdir), failures)
        if tv is not None:
            dep_score = trivy.dependency_score(
                critical=tv.critical, high=tv.high, medium=tv.medium, low=tv.low
            )
            findings.extend(_trivy_findings(tv))
            _persist_artifact(scan_id, "trivy", tv.raw)
            succeeded.add("trivy")
        else:
            dep_score = NEUTRAL_DEPENDENCY_SCORE

        # ── phase 2g: complexity ─────────────────────────────────
        cx = _safe("complexity", lambda: complexity.run(workdir), failures)
        if cx is not None:
            cx_score = complexity.complexity_score(cx.avg_complexity)
            breakdown["avg_complexity"] = round(cx.avg_complexity, 2)
            succeeded.add("lizard")
        else:
            cx_score = NEUTRAL_COMPLEXITY_SCORE

        # ── phase 2h: duplication ────────────────────────────────
        dup = _safe("duplication", lambda: duplication.run(workdir), failures)
        if dup is not None:
            dup_score = duplication.duplication_score(dup.duplication_percent)
            breakdown["duplication_percent"] = round(dup.duplication_percent, 2)
            succeeded.add("jscpd")
        else:
            dup_score = NEUTRAL_DUPLICATION_SCORE

        # ── phase 2i: lint ───────────────────────────────────────
        lt = _safe("lint", lambda: lint.run(workdir, languages), failures)
        if lt is not None and lt.total_issues >= 0 and (lt.by_language or loc > 0):
            lint_score = lint.lint_density_score(total_issues=lt.total_issues, loc=loc)
            breakdown["lint_issues"] = lt.total_issues
        else:
            lint_score = NEUTRAL_LINT_SCORE

    # workdir cleaned up — clone context exited.

    # ── phase 3: scoring (off-workdir engines + formula) ─────────
    _phase("scoring")

    # ── 3a: scorecard ────────────────────────────────────────────
    sc = _safe("scorecard", lambda: scorecard.fetch_or_run(owner, name), failures)
    if sc is not None:
        sc_aggregate = sc.aggregate
        _persist_artifact(scan_id, "scorecard", sc.raw)
        succeeded.add("scorecard")
    else:
        sc_aggregate = NEUTRAL_SCORECARD_AGGREGATE

    # ── 3b: community signals ───────────────────────────────────
    com_sig = _safe(
        "community",
        lambda: community.collect(owner, name, stars=meta.stars, pushed_at=meta.pushed_at),
        failures,
        default=community.CommunitySignals(stars=meta.stars),
    )

    # ── 3c: compose sub-scores via formula ───────────────────────
    sec, sec_bd = _compute_security(sc_aggregate, sem_score, dep_score)
    qual, qual_bd = _compute_quality(cx_score, lint_score, dup_score, ts.score, file_size_s)
    comm, comm_bd = _compute_community(com_sig)
    total, grade = overall_score(sec, qual, hyg_score, comm)

    breakdown.update(sec_bd | qual_bd | comm_bd)

    # Build tool_versions from the registry — single source of truth for
    # version detection across the codebase.
    tool_vers = detect_versions(succeeded)
    tool_vers["formula"] = FORMULA_VERSION

    return PipelineResult(
        security=sec,
        quality=qual,
        hygiene=hyg_score,
        community=comm,
        overall=total,
        grade=grade,
        breakdown=breakdown,
        findings=findings[:_FINDINGS_CAP_TOTAL],
        failures=failures,
        tool_versions=tool_vers,
        commit_sha=commit_sha,
        artifacts_url=_artifacts_url(scan_id),
        partial=bool(failures),
    )
