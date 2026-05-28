"""OpenSSF Scorecard integration.

Strategy (docs/03 §1a):
    1. Try api.scorecard.dev for cached scorecard.
    2. If unavailable, run the `scorecard` binary locally.
    3. Parse aggregate score (0-10) and per-check breakdown.
"""
import json
import logging
import os
from dataclasses import dataclass, field

import httpx

from stackhealth.engines._tools import EngineFailed, EngineUnavailable, require, run_capture

log = logging.getLogger(__name__)


@dataclass
class ScorecardResult:
    aggregate: float  # 0-10
    checks: dict[str, float] = field(default_factory=dict)  # check_name -> score (0-10, -1 unknown)
    raw: dict = field(default_factory=dict)
    source: str = "api"  # 'api' or 'binary'


def _from_api(owner: str, name: str) -> ScorecardResult | None:
    url = f"https://api.scorecard.dev/projects/github.com/{owner}/{name}"
    try:
        r = httpx.get(url, timeout=10.0)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    data = r.json()
    aggregate = float(data.get("score", -1))
    if aggregate < 0:
        return None
    checks = {
        c.get("name", "?"): float(c.get("score", -1))
        for c in data.get("checks", [])
    }
    return ScorecardResult(aggregate=aggregate, checks=checks, raw=data, source="api")


def _from_binary(owner: str, name: str) -> ScorecardResult:
    require("scorecard")
    env = os.environ.copy()
    if not env.get("GITHUB_AUTH_TOKEN") and env.get("GITHUB_TOKEN"):
        env["GITHUB_AUTH_TOKEN"] = env["GITHUB_TOKEN"]
    proc = run_capture(
        [
            "scorecard",
            f"--repo=github.com/{owner}/{name}",
            "--format=json",
            "--show-details",
        ],
        timeout=180,
    )
    if not proc.stdout.strip():
        raise EngineFailed(f"scorecard produced no output; stderr: {proc.stderr[:200]}")
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise EngineFailed(f"scorecard returned invalid JSON: {e}") from e

    aggregate = float(data.get("score", -1))
    checks = {c.get("name", "?"): float(c.get("score", -1)) for c in data.get("checks", [])}
    return ScorecardResult(aggregate=aggregate, checks=checks, raw=data, source="binary")


def fetch_or_run(owner: str, name: str) -> ScorecardResult:
    api = _from_api(owner, name)
    if api is not None:
        return api
    try:
        return _from_binary(owner, name)
    except EngineUnavailable:
        # Binary not present locally — re-raise so worker marks partial.
        raise
