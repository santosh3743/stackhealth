"""LoC by language via `cloc --json`.

Reference: docs/03-SCORING-METHODOLOGY.md §2e (file size), §1b normalisation.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, require, run_capture

log = logging.getLogger(__name__)


@dataclass
class ClocResult:
    total_loc: int = 0
    by_language: dict[str, int] = field(default_factory=dict)
    mega_files: int = 0
    raw: dict = field(default_factory=dict)


def run(workdir: Path) -> ClocResult:
    binpath = require("cloc")
    proc = run_capture(
        [binpath, "--json", "--quiet", "--by-file-by-lang", str(workdir)],
        timeout=120,
    )
    if not proc.stdout.strip():
        raise EngineFailed("cloc produced no output")
    # cloc with `--by-file-by-lang` on very large or unusual repos
    # occasionally emits a trailing warning or a second JSON object after
    # the main report (seen on novuhq/novu — 38k file entries followed
    # by extra text). `json.loads` rejects anything after the first
    # document. `JSONDecoder.raw_decode` reads just the first one and
    # tells us where it ended; we discard the tail.
    try:
        data, end = json.JSONDecoder().raw_decode(proc.stdout.lstrip())
    except json.JSONDecodeError as e:
        raise EngineFailed(f"cloc returned invalid JSON: {e}") from e
    if end < len(proc.stdout.lstrip()):
        log.warning(
            "cloc produced trailing data after JSON (%d bytes); ignoring", len(proc.stdout) - end
        )

    by_file = data.get("by_file", {})
    by_lang = data.get("by_lang", {})

    by_language = {
        lang: int(stats.get("code", 0))
        for lang, stats in by_lang.items()
        if isinstance(stats, dict) and lang not in ("header", "SUM")
    }
    total_loc = int(data.get("SUM", {}).get("code", sum(by_language.values())))
    mega_files = sum(
        1
        for path, stats in by_file.items()
        if isinstance(stats, dict)
        and path not in ("header", "SUM")
        and int(stats.get("code", 0)) > 1000
    )
    return ClocResult(
        total_loc=total_loc,
        by_language=by_language,
        mega_files=mega_files,
        raw=data,
    )


def file_size_score(mega_files: int) -> int:
    """Per docs §2e: penalise files >1000 LoC."""
    return max(0, 100 - mega_files * 5)
