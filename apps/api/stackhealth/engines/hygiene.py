"""Hygiene engine — the binary checklist.

Reference: docs/03-SCORING-METHODOLOGY.md §3 (Hygiene score).
"""
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# OSI-approved SPDX list (subset; expand as needed).
OSI_APPROVED = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "GPL-2.0-only", "GPL-2.0-or-later",
    "GPL-3.0-only", "GPL-3.0-or-later", "LGPL-2.1-only", "LGPL-3.0-only", "MPL-2.0",
    "ISC", "Unlicense", "CC0-1.0", "AGPL-3.0-only", "EPL-2.0", "BSL-1.0",
}


@dataclass
class HygieneResult:
    score: int
    breakdown: dict[str, int] = field(default_factory=dict)


def _has_file(workdir: Path, name: str, min_size: int = 0) -> bool:
    for p in workdir.glob(name):
        if p.is_file() and p.stat().st_size >= min_size:
            return True
    return False


def _ci_present(workdir: Path) -> tuple[bool, bool]:
    """Returns (any_ci, has_pr_trigger)."""
    gh = workdir / ".github" / "workflows"
    gl = workdir / ".gitlab-ci.yml"
    any_ci = (gh.is_dir() and any(gh.glob("*.yml"))) or gl.is_file()
    pr = False
    if gh.is_dir():
        for f in gh.glob("*.yml"):
            try:
                data = yaml.safe_load(f.read_text())
            except yaml.YAMLError:
                continue
            on = (data or {}).get("on") or (data or {}).get(True)
            if isinstance(on, dict) and "pull_request" in on:
                pr = True
                break
            if isinstance(on, list) and "pull_request" in on:
                pr = True
                break
            if on == "pull_request":
                pr = True
                break
    return any_ci, pr


def _tests_dir(workdir: Path) -> bool:
    for name in ("tests", "test", "__tests__", "spec"):
        if (workdir / name).is_dir():
            return True
    return False


def evaluate(
    workdir: Path,
    *,
    license_spdx: str | None,
    has_description: bool,
    has_topics: bool,
    days_since_last_commit: int | None,
) -> HygieneResult:
    """Score per docs/03-SCORING-METHODOLOGY.md §3. Max 100."""
    b: dict[str, int] = {}

    b["readme"] = 15 if _has_file(workdir, "README*", min_size=300) else 0
    b["license_file"] = 15 if _has_file(workdir, "LICENSE*") else 0
    b["license_osi"] = 5 if license_spdx in OSI_APPROVED else 0
    b["contributing"] = 8 if _has_file(workdir, "CONTRIBUTING*") else 0
    b["code_of_conduct"] = 5 if _has_file(workdir, "CODE_OF_CONDUCT*") else 0
    b["security_md"] = 7 if _has_file(workdir, "SECURITY*") else 0

    any_ci, pr_trigger = _ci_present(workdir)
    b["ci_present"] = 10 if any_ci else 0
    b["ci_pr_trigger"] = 5 if pr_trigger else 0

    b["tests_dir"] = 10 if _tests_dir(workdir) else 0
    b["gitignore"] = 3 if _has_file(workdir, ".gitignore") else 0
    b["description"] = 5 if has_description else 0
    b["topics"] = 5 if has_topics else 0
    b["recent_commit"] = 7 if (days_since_last_commit is not None and days_since_last_commit < 365) else 0

    return HygieneResult(score=sum(b.values()), breakdown=b)
