"""Copy-paste duplication via `jscpd`. Reference: docs/03 §2c."""
import json
import logging
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, EngineUnavailable, run_capture

log = logging.getLogger(__name__)


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


def run(workdir: Path, timeout: int = 180) -> DuplicationResult:
    cmd_prefix = _resolve_jscpd()
    with tempfile.TemporaryDirectory(prefix="sh-jscpd-") as outdir:
        proc = run_capture(
            cmd_prefix
            + [
                "--mode", "mild",
                "--silent",
                "--reporters", "json",
                "--output", outdir,
                str(workdir),
            ],
            timeout=timeout,
        )
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
