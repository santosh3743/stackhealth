"""Cyclomatic complexity via `lizard` (multi-language). Reference: docs/03 §2a."""
import csv
import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

from stackhealth.engines._tools import EngineFailed, require, run_capture

log = logging.getLogger(__name__)


@dataclass
class ComplexityResult:
    avg_complexity: float = 0.0
    function_count: int = 0
    high_complexity_funcs: int = 0  # CCN > 15
    raw: dict = field(default_factory=dict)


def run(workdir: Path, timeout: int = 90) -> ComplexityResult:
    require("lizard")
    proc = run_capture(
        ["lizard", "--csv", "--working_threads", "4", str(workdir)],
        timeout=timeout,
    )
    if not proc.stdout.strip():
        raise EngineFailed("lizard produced no output")

    reader = csv.reader(io.StringIO(proc.stdout))
    ccns: list[int] = []
    for row in reader:
        # lizard CSV columns: NLOC,CCN,token,PARAM,length,location,...
        if len(row) < 2:
            continue
        try:
            ccn = int(row[1])
        except ValueError:
            continue
        ccns.append(ccn)

    if not ccns:
        return ComplexityResult()

    avg = sum(ccns) / len(ccns)
    return ComplexityResult(
        avg_complexity=avg,
        function_count=len(ccns),
        high_complexity_funcs=sum(1 for c in ccns if c > 15),
        raw={"function_ccns_sample": ccns[:50]},
    )


def complexity_score(avg_complexity: float) -> int:
    """Per docs §2a: avg ≤5 → 100. Each point above 5 costs 8."""
    if avg_complexity <= 5:
        return 100
    return max(0, round(100 - (avg_complexity - 5) * 8))
