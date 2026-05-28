"""Trivy filesystem dependency scan. Reference: docs/03 §1c."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, require, run_capture

log = logging.getLogger(__name__)


@dataclass
class TrivyFinding:
    vulnerability_id: str
    severity: str  # CRITICAL/HIGH/MEDIUM/LOW
    package: str
    installed_version: str
    fixed_version: str | None
    title: str
    file_path: str


@dataclass
class TrivyResult:
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    findings: list[TrivyFinding] = field(default_factory=list)
    raw: dict = field(default_factory=dict)


def run(workdir: Path, timeout: int = 180) -> TrivyResult:
    binpath = require("trivy")
    proc = run_capture(
        [
            binpath,
            "fs",
            "--scanners",
            "vuln",
            "--format",
            "json",
            "--quiet",
            "--severity",
            "CRITICAL,HIGH,MEDIUM,LOW",
            str(workdir),
        ],
        timeout=timeout,
    )
    if not proc.stdout.strip():
        raise EngineFailed(f"trivy produced no JSON; stderr: {proc.stderr[:200]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise EngineFailed(f"trivy returned invalid JSON: {e}") from e

    result = TrivyResult(raw=data)
    for target in data.get("Results", []) or []:
        target_path = target.get("Target", "")
        for v in target.get("Vulnerabilities", []) or []:
            sev = (v.get("Severity") or "").upper()
            if sev == "CRITICAL":
                result.critical += 1
            elif sev == "HIGH":
                result.high += 1
            elif sev == "MEDIUM":
                result.medium += 1
            elif sev == "LOW":
                result.low += 1
            result.findings.append(
                TrivyFinding(
                    vulnerability_id=v.get("VulnerabilityID", "unknown"),
                    severity=sev,
                    package=v.get("PkgName", ""),
                    installed_version=v.get("InstalledVersion", ""),
                    fixed_version=v.get("FixedVersion"),
                    title=(v.get("Title") or v.get("Description") or "")[:500],
                    file_path=target_path,
                )
            )
    return result


def dependency_score(*, critical: int, high: int, medium: int, low: int) -> int:
    """Per docs §1c: absolute CVE penalty (no LoC norm)."""
    penalty = 20 * critical + 8 * high + 3 * medium + 1 * low
    return max(0, 100 - penalty)
