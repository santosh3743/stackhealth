"""Language-dispatched lint runner. Reference: docs/03 §2b.

Each language linter is independent — if its binary is missing or the language
isn't present, it contributes 0 issues and is omitted from `by_language`.
"""
import json
import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, run_capture

log = logging.getLogger(__name__)


@dataclass
class LintResult:
    total_issues: int = 0
    by_language: dict[str, int] = field(default_factory=dict)
    raw: dict = field(default_factory=dict)


def _ruff(workdir: Path) -> int:
    if not shutil.which("ruff"):
        return -1
    proc = run_capture(
        ["ruff", "check", "--output-format=json", "--exit-zero", str(workdir)],
        timeout=60,
    )
    if not proc.stdout.strip():
        return 0
    try:
        return len(json.loads(proc.stdout))
    except json.JSONDecodeError as e:
        raise EngineFailed(f"ruff json parse failed: {e}") from e


def _eslint(workdir: Path) -> int:
    # Only run if the project actually has an eslint config; otherwise eslint
    # fails noisily on every JS file. Heuristic: look for any of the standard configs.
    candidates = [
        ".eslintrc", ".eslintrc.json", ".eslintrc.js", ".eslintrc.cjs",
        ".eslintrc.yaml", ".eslintrc.yml", "eslint.config.js", "eslint.config.mjs",
    ]
    if not any((workdir / c).exists() for c in candidates):
        return -1
    if not shutil.which("eslint"):
        return -1
    proc = run_capture(
        ["eslint", ".", "--format", "json", "--no-error-on-unmatched-pattern"],
        cwd=workdir,
        timeout=120,
    )
    if not proc.stdout.strip():
        return 0
    try:
        files = json.loads(proc.stdout)
        return sum(f.get("errorCount", 0) + f.get("warningCount", 0) for f in files)
    except json.JSONDecodeError as e:
        raise EngineFailed(f"eslint json parse failed: {e}") from e


def _golangci(workdir: Path) -> int:
    if not (workdir / "go.mod").exists():
        return -1
    if not shutil.which("golangci-lint"):
        return -1
    proc = run_capture(
        ["golangci-lint", "run", "--out-format=json", "--issues-exit-code=0", "./..."],
        cwd=workdir,
        timeout=120,
    )
    if not proc.stdout.strip():
        return 0
    try:
        return len(json.loads(proc.stdout).get("Issues", []) or [])
    except json.JSONDecodeError:
        return 0


_RUNNERS: dict[str, callable] = {
    "Python": _ruff,
    "JavaScript": _eslint,
    "TypeScript": _eslint,
    "Go": _golangci,
}


def run(workdir: Path, languages: list[str]) -> LintResult:
    result = LintResult()
    seen_runners: set = set()
    for lang in languages:
        runner = _RUNNERS.get(lang)
        if runner is None or runner in seen_runners:
            continue
        seen_runners.add(runner)
        try:
            n = runner(workdir)
        except Exception as e:  # noqa: BLE001
            log.warning("lint runner for %s failed: %s", lang, e)
            continue
        if n < 0:
            continue
        result.by_language[lang] = n
        result.total_issues += n
    return result


def lint_density_score(*, total_issues: int, loc: int) -> int:
    """Per docs §2b. Returns 100 if loc is 0 (avoid div-by-zero)."""
    if loc <= 0:
        return 100
    issues_per_kloc = total_issues / (loc / 1000)
    return max(0, round(100 - issues_per_kloc * 2))
