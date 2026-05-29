"""Copy-paste duplication via `jscpd`. Reference: docs/03 §2c.

jscpd is O(n²)-ish over the input, so on big repos (anything with a lot
of generated/vendored content) we need to be aggressive about what we
let it look at. The `--gitignore` flag plus an explicit ignore list of
common bloat patterns (lockfiles, fixture trees, minified bundles, etc.)
keeps the run tractable on 10M-LoC monsters like swc-project/swc.
"""

import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, EngineUnavailable, run_capture

log = logging.getLogger(__name__)


# Path globs jscpd should skip even when the repo doesn't gitignore them.
# These are universally non-source — duplicates inside them either don't
# matter (lockfiles, minified bundles) or actively distort the score
# (test fixtures of intentionally similar inputs).
_DEFAULT_IGNORES = (
    "**/node_modules/**",
    "**/vendor/**",
    "**/dist/**",
    "**/build/**",
    "**/target/**",  # Rust
    "**/.next/**",
    "**/.turbo/**",
    "**/__pycache__/**",
    "**/*.lock",
    "**/*.lockb",
    "**/package-lock.json",
    "**/pnpm-lock.yaml",
    "**/yarn.lock",
    "**/Cargo.lock",
    "**/poetry.lock",
    "**/uv.lock",
    "**/Pipfile.lock",
    "**/composer.lock",
    "**/Gemfile.lock",
    "**/go.sum",
    "**/*.min.js",
    "**/*.min.css",
    "**/*.bundle.js",
    "**/*.map",
    # Common test-fixture directories — jscpd duplicates here are
    # intentional (snapshot baselines, parser corner-case grids).
    "**/__fixtures__/**",
    "**/fixtures/**",
    "**/__snapshots__/**",
    "**/testdata/**",
    # SVG icon sets often share large repeated paths — not real dup.
    "**/*.svg",
)


@dataclass
class DuplicationResult:
    duplication_percent: float = 0.0
    duplicate_blocks: int = 0
    raw: dict = field(default_factory=dict)


def _resolve_jscpd() -> list[str]:
    """jscpd may be installed as a global binary or only via npx."""
    if shutil.which("jscpd"):
        return ["jscpd"]
    if shutil.which("npx"):
        return ["npx", "--yes", "jscpd"]
    raise EngineUnavailable("jscpd not found (install via npm i -g jscpd, or have npx available)")


def run(workdir: Path, timeout: int = 600) -> DuplicationResult:
    """Run jscpd over `workdir`. Default timeout is 10 min — enough for
    repos in the 1-10M LoC range with our ignore list applied.
    """
    cmd_prefix = _resolve_jscpd()
    with tempfile.TemporaryDirectory(prefix="sh-jscpd-") as outdir:
        cmd = cmd_prefix + [
            "--mode",
            "mild",
            "--silent",
            "--reporters",
            "json",
            "--output",
            outdir,
            # Respect the repo's own .gitignore — it almost always
            # excludes the build outputs we'd otherwise re-list.
            "--gitignore",
            # Glob-based safety net for things the gitignore misses.
            "--ignore",
            ",".join(_DEFAULT_IGNORES),
            str(workdir),
        ]
        proc = run_capture(cmd, timeout=timeout)
        report_path = Path(outdir) / "jscpd-report.json"
        if not report_path.exists():
            # jscpd exited but didn't write a report — likely no source files matched.
            if proc.returncode != 0 and not proc.stdout:
                raise EngineFailed(f"jscpd failed: {proc.stderr[:200]}")
            return DuplicationResult()
        try:
            data = json.loads(report_path.read_text())
        except json.JSONDecodeError as e:
            raise EngineFailed(f"jscpd json parse failed: {e}") from e

    stats = data.get("statistics", {}).get("total", {})
    percent = float(stats.get("percentage", 0.0))
    return DuplicationResult(
        duplication_percent=percent,
        duplicate_blocks=int(stats.get("duplicates", 0)),
        raw=data,
    )


def duplication_score(duplication_percent: float) -> int:
    """Per docs §2c: 0% dup → 100. 20% dup → 0."""
    return max(0, round(100 - duplication_percent * 5))
