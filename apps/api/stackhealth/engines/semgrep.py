"""Semgrep p/security-audit runner. Reference: docs/03 §1b."""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, require, run_capture

log = logging.getLogger(__name__)


@dataclass
class SemgrepFinding:
    rule_id: str
    severity: str  # 'ERROR' / 'WARNING' / 'INFO'
    message: str
    file_path: str
    line: int


@dataclass
class SemgrepResult:
    errors: int = 0
    warnings: int = 0
    info: int = 0
    findings: list[SemgrepFinding] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def run(workdir: Path, timeout: int = 90) -> SemgrepResult:
    binpath = require("semgrep")
    proc = run_capture(
        [
            binpath, "scan",
            "--config", "p/security-audit",
            "--json", "--quiet",
            "--timeout", "60",
            "--metrics", "off",
            "--no-git-ignore",
            str(workdir),
        ],
        timeout=timeout,
    )
    # semgrep exits non-zero when findings are present — that's normal.
    if not proc.stdout.strip():
        raise EngineFailed(f"semgrep produced no JSON; stderr: {proc.stderr[:200]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise EngineFailed(f"semgrep returned invalid JSON: {e}") from e

    results = data.get("results", [])
    findings: list[SemgrepFinding] = []
    errors = warnings = info = 0
    for r in results:
        sev = (r.get("extra", {}).get("severity") or "INFO").upper()
        if sev == "ERROR":
            errors += 1
        elif sev == "WARNING":
            warnings += 1
        else:
            info += 1
        findings.append(
            SemgrepFinding(
                rule_id=r.get("check_id", "unknown"),
                severity=sev,
                message=(r.get("extra", {}).get("message") or "")[:1000],
                file_path=str(Path(r.get("path", "")).relative_to(workdir))
                if r.get("path", "").startswith(str(workdir))
                else r.get("path", ""),
                line=int(r.get("start", {}).get("line", 0) or 0),
            )
        )

    return SemgrepResult(
        errors=errors, warnings=warnings, info=info,
        findings=findings, raw=data,
    )


def semgrep_score(*, errors: int, warnings: int, info: int, loc: int) -> int:
    """Per docs §1b: LoC-normalised penalty."""
    penalty = 8 * errors + 3 * warnings + 1 * info
    return max(0, round(100 - penalty / (loc / 1000 + 1)))
