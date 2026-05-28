"""Community sub-scores (activity, contributors, popularity, responsiveness).

Reference: docs/03 §4. All GitHub REST calls go through `_gh`.
"""

import logging
import math
import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

import httpx

from stackhealth.config import settings

log = logging.getLogger(__name__)


@dataclass
class CommunitySignals:
    days_since_last_commit: int | None = None
    commits_last_90d: int = 0
    contributors_last_365d: int = 0
    stars: int = 0
    median_first_response_hours: float | None = None
    issues_in_90d: int = 0
    raw: dict = field(default_factory=dict)


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def _gh(path: str, params: dict | None = None) -> httpx.Response:
    url = f"https://api.github.com{path}"
    return httpx.get(url, headers=_headers(), params=params, timeout=15.0)


def collect(owner: str, name: str, *, stars: int, pushed_at: datetime | None) -> CommunitySignals:
    sig = CommunitySignals(stars=stars)
    now = datetime.now(UTC)
    since_90 = now - timedelta(days=90)
    since_365 = now - timedelta(days=365)

    if pushed_at is not None:
        sig.days_since_last_commit = (now - pushed_at).days

    # commits in last 90 days
    try:
        r = _gh(
            f"/repos/{owner}/{name}/commits",
            {"since": since_90.isoformat(), "per_page": 100},
        )
        if r.status_code == 200:
            commits = r.json()
            sig.commits_last_90d = len(commits)
            # If exactly 100 returned, there might be more — we cap at 100 for scoring.
    except httpx.HTTPError as e:
        log.warning("commits api failed: %s", e)

    # contributors in last year — use participation endpoint for weekly stats
    try:
        r = _gh(f"/repos/{owner}/{name}/stats/contributors")
        if r.status_code == 200:
            data = r.json() or []
            active: set[str] = set()
            cutoff = since_365.timestamp()
            for c in data:
                weeks = c.get("weeks", []) or []
                if any(w.get("w", 0) >= cutoff and w.get("c", 0) > 0 for w in weeks):
                    login = (c.get("author") or {}).get("login")
                    if login:
                        active.add(login)
            sig.contributors_last_365d = len(active)
    except httpx.HTTPError as e:
        log.warning("contributors api failed: %s", e)

    # responsiveness: median first-response on issues opened in last 90 days
    try:
        r = _gh(
            f"/repos/{owner}/{name}/issues",
            {
                "state": "all",
                "since": since_90.isoformat(),
                "per_page": 30,
                "sort": "created",
                "direction": "desc",
            },
        )
        if r.status_code == 200:
            issues = [i for i in r.json() if "pull_request" not in i]
            sig.issues_in_90d = len(issues)
            response_hours: list[float] = []
            for issue in issues[:20]:  # cap to keep API budget reasonable
                comments_url = issue.get("comments_url")
                created = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))
                if issue.get("comments", 0) == 0 or not comments_url:
                    continue
                cr = httpx.get(
                    comments_url,
                    headers=_headers(),
                    params={"per_page": 1},
                    timeout=10.0,
                )
                if cr.status_code != 200:
                    continue
                comments = cr.json()
                if not comments:
                    continue
                first = datetime.fromisoformat(comments[0]["created_at"].replace("Z", "+00:00"))
                response_hours.append((first - created).total_seconds() / 3600.0)
            if response_hours:
                sig.median_first_response_hours = statistics.median(response_hours)
    except httpx.HTTPError as e:
        log.warning("issues api failed: %s", e)

    return sig


def activity_score(*, days_since_last_commit: int | None, commits_last_90d: int) -> int:
    if days_since_last_commit is None or days_since_last_commit > 365:
        return 0
    if days_since_last_commit > 180:
        return 30
    return min(100, 40 + commits_last_90d * 2)


def contributor_score(contributors: int) -> int:
    return min(100, round(math.log2(contributors + 1) * 25))


def popularity_score(stars: int) -> int:
    return min(100, round(math.log10(stars + 1) * 25))


def responsiveness_score(median_hours: float | None, issues_in_90d: int) -> int:
    if median_hours is None:
        return 70 if issues_in_90d == 0 else 60
    if median_hours < 24:
        return 100
    if median_hours < 72:
        return 80
    if median_hours < 168:
        return 60
    if median_hours < 720:
        return 30
    return 0
