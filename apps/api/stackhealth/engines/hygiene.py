"""Hygiene engine — the binary checklist.

Reference: docs/03-SCORING-METHODOLOGY.md §3 (Hygiene score).
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

# OSI-approved SPDX list (subset; expand as needed).
OSI_APPROVED = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "GPL-2.0-only",
    "GPL-2.0-or-later",
    "GPL-3.0-only",
    "GPL-3.0-or-later",
    "LGPL-2.1-only",
    "LGPL-3.0-only",
    "MPL-2.0",
    "ISC",
    "Unlicense",
    "CC0-1.0",
    "AGPL-3.0-only",
    "EPL-2.0",
    "BSL-1.0",
}

# Directory names commonly used for test suites.
_TEST_DIR_NAMES = ("tests", "test", "__tests__", "spec")

# Common monorepo workspace prefixes that contain per-package tests directories.
# Order matters only insofar as we check cheaper paths first.
_MONOREPO_PREFIXES = (
    "apps/*",
    "packages/*",
    "services/*",
    "libs/*",
    "modules/*",
    "crates/*",  # Rust workspaces
)


# Substring fingerprints unique enough to identify a license from its body
# text alone. Used when GitHub's licensee can't auto-detect because of
# preamble text or a non-standard header. Order matters — Apache must come
# before AGPL/GPL because both contain "GENERAL PUBLIC LICENSE".
_LICENSE_FINGERPRINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    # (SPDX, fingerprint substrings — all must appear)
    ("MIT", ("Permission is hereby granted, free of charge",)),
    ("Apache-2.0", ("Apache License", "Version 2.0", "http://www.apache.org/licenses/")),
    (
        "BSD-3-Clause",
        ("Redistributions of source code", "Neither the name"),
    ),
    (
        "BSD-2-Clause",
        ("Redistributions of source code", "Redistributions in binary form"),
    ),
    ("ISC", ("Permission to use, copy, modify, and/or distribute",)),
    ("Unlicense", ("This is free and unencumbered software released into the public domain",)),
    ("CC0-1.0", ("CC0 1.0 Universal",)),
    ("MPL-2.0", ("Mozilla Public License Version 2.0",)),
    ("AGPL-3.0-only", ("GNU AFFERO GENERAL PUBLIC LICENSE", "Version 3")),
    ("GPL-3.0-only", ("GNU GENERAL PUBLIC LICENSE", "Version 3")),
    ("GPL-2.0-only", ("GNU GENERAL PUBLIC LICENSE", "Version 2")),
    ("LGPL-3.0-only", ("GNU LESSER GENERAL PUBLIC LICENSE", "Version 3")),
    ("LGPL-2.1-only", ("GNU LESSER GENERAL PUBLIC LICENSE", "Version 2.1")),
    ("EPL-2.0", ("Eclipse Public License", "v. 2.0")),
    ("BSL-1.0", ("Boost Software License", "Version 1.0")),
)


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
    """True if a tests/ (or variant) directory exists anywhere reasonable.

    Looks at:
      1. The repo root (covers single-package repos).
      2. One level inside common monorepo workspace dirs
         (apps/*/tests/, packages/*/tests/, services/*/tests/, …)

    We deliberately stop at depth 2 — going deeper invites false positives
    from vendored dependencies, fixtures, etc.
    """
    # 1. Root-level.
    for name in _TEST_DIR_NAMES:
        if (workdir / name).is_dir():
            return True

    # 2. Monorepo workspaces.
    for pattern in _MONOREPO_PREFIXES:
        for child in workdir.glob(pattern):
            if not child.is_dir():
                continue
            for name in _TEST_DIR_NAMES:
                if (child / name).is_dir():
                    return True
    return False


def _detect_spdx_from_license_file(workdir: Path) -> str | None:
    """Read LICENSE* and return an SPDX identifier if we recognise the body.

    Falls back from / complements GitHub's `license_spdx`, which returns
    `NOASSERTION` whenever the licensee can't make a clean match because
    of a custom preamble or non-standard header.
    """
    # Find the first LICENSE-ish file. Don't read whole tree — root only.
    candidates: list[Path] = []
    for pattern in ("LICENSE", "LICENSE.*", "LICENSE-*", "COPYING", "COPYING.*"):
        candidates.extend(workdir.glob(pattern))
    if not candidates:
        return None
    # Take the largest as a tie-breaker; LICENSE.md/LICENSE.txt often have
    # the full text while bare LICENSE may be a stub on some projects.
    candidates.sort(key=lambda p: p.stat().st_size if p.is_file() else 0, reverse=True)

    try:
        text = candidates[0].read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    # First 8 KiB is plenty — every standard licence header fits well within.
    sample = text[:8192]
    for spdx, fingerprints in _LICENSE_FINGERPRINTS:
        if all(fp in sample for fp in fingerprints):
            return spdx
    return None


def _resolve_license_spdx(workdir: Path, github_provided: str | None) -> str | None:
    """Prefer GitHub's detection when it succeeded; fall back to body sniffing.

    NOASSERTION and "NONE" are both treated as "GitHub didn't recognise it",
    which is when our local sniffing earns its keep.
    """
    if github_provided and github_provided not in {"NOASSERTION", "NONE"}:
        return github_provided
    return _detect_spdx_from_license_file(workdir)


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

    effective_spdx = _resolve_license_spdx(workdir, license_spdx)

    b["readme"] = 15 if _has_file(workdir, "README*", min_size=300) else 0
    b["license_file"] = 15 if _has_file(workdir, "LICENSE*") else 0
    b["license_osi"] = 5 if effective_spdx in OSI_APPROVED else 0
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
    b["recent_commit"] = (
        7 if (days_since_last_commit is not None and days_since_last_commit < 365) else 0
    )

    return HygieneResult(score=sum(b.values()), breakdown=b)
