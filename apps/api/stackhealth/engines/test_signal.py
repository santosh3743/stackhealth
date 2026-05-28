"""Test presence signals (no actual test execution). Reference: docs/03 §2d.

We score test *presence*:
- tests/ test/ __tests__/ spec/ directory or *_test.go / *.test.ts files → +40
- pytest/jest/mocha/go test/cargo test in CI config → +30
- coverage badge in README or coverage report file → +20
- codecov.yml / coverage.xml present → +10
"""
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class TestSignalResult:
    score: int = 0
    breakdown: dict[str, int] = field(default_factory=dict)


_TEST_DIRS = ("tests", "test", "__tests__", "spec")
_TEST_FILE_RE = re.compile(
    r"(.*/)?("
    r"test_[^/]+\.py"
    r"|[^/]+_test\.py"
    r"|[^/]+_test\.go"
    r"|[^/]+\.test\.(ts|tsx|js|jsx)"
    r"|[^/]+\.spec\.(ts|tsx|js|jsx)"
    r")$"
)
_CI_RUNNERS = ("pytest", "jest", "mocha", "go test", "cargo test", "vitest", "rspec")


def _has_test_dir_or_files(workdir: Path) -> bool:
    for d in _TEST_DIRS:
        if (workdir / d).is_dir():
            return True
    # Walk a bounded number of files looking for a test file pattern.
    count = 0
    for p in workdir.rglob("*"):
        if not p.is_file():
            continue
        count += 1
        if count > 5000:
            break
        if _TEST_FILE_RE.match(str(p.relative_to(workdir))):
            return True
    return False


def _ci_mentions_test_runner(workdir: Path) -> bool:
    workflows = workdir / ".github" / "workflows"
    candidates: list[Path] = []
    if workflows.is_dir():
        candidates.extend(workflows.glob("*.yml"))
        candidates.extend(workflows.glob("*.yaml"))
    for extra in (".gitlab-ci.yml", "circle.yml", ".circleci/config.yml"):
        p = workdir / extra
        if p.is_file():
            candidates.append(p)
    for p in candidates:
        try:
            text = p.read_text(errors="ignore").lower()
        except OSError:
            continue
        if any(r in text for r in _CI_RUNNERS):
            return True
    return False


def _readme_has_coverage_badge(workdir: Path) -> bool:
    for p in workdir.glob("README*"):
        try:
            text = p.read_text(errors="ignore").lower()
        except OSError:
            continue
        if "codecov.io" in text or "coveralls.io" in text or "shields.io/coverage" in text:
            return True
    return False


def _coverage_config_present(workdir: Path) -> bool:
    for name in ("codecov.yml", ".codecov.yml", "coverage.xml", ".coveragerc"):
        if (workdir / name).is_file():
            return True
    return False


def run(workdir: Path) -> TestSignalResult:
    b: dict[str, int] = {}
    b["test_files"] = 40 if _has_test_dir_or_files(workdir) else 0
    b["ci_test_runner"] = 30 if _ci_mentions_test_runner(workdir) else 0
    b["coverage_badge"] = 20 if _readme_has_coverage_badge(workdir) else 0
    b["coverage_config"] = 10 if _coverage_config_present(workdir) else 0
    return TestSignalResult(score=min(100, sum(b.values())), breakdown=b)
