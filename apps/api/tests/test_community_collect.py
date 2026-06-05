"""Coverage for the GitHub-API-touching parts of community.collect().

We monkeypatch the module-level `_gh` and `httpx.get` so no network is
hit. The behaviours we want to lock in:

  * `/stats/contributors` returning HTTP 202 is retried, not silently
    swallowed.
  * If retries never warm up, contributors_last_365d falls back to
    distinct authors from the 90-day commits payload (instead of 0).
  * The fallback handles anonymous commits via the commit-author email.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from stackhealth.engines import community


class _StubResponse:
    def __init__(self, status_code: int, payload: Any = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep the retry tests instant.
    monkeypatch.setattr(community.time, "sleep", lambda _s: None)


def _fake_commits(logins: list[str | None]) -> list[dict]:
    out: list[dict] = []
    for i, login in enumerate(logins):
        if login is None:
            out.append(
                {
                    "author": None,
                    "commit": {"author": {"email": f"ghost{i}@example.com"}},
                }
            )
        else:
            out.append({"author": {"login": login}, "commit": {"author": {"email": ""}}})
    return out


def test_contributors_warm_cache_uses_stats_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    commits = _fake_commits(["alice", "bob"])
    stats_payload = [
        {
            "author": {"login": login},
            "weeks": [{"w": int(datetime.now(UTC).timestamp()), "c": 1}],
        }
        for login in ("alice", "bob", "carol", "dave", "erin")
    ]
    calls: list[str] = []

    def _gh(path: str, params: dict | None = None) -> _StubResponse:
        calls.append(path)
        if path.endswith("/commits"):
            return _StubResponse(200, commits)
        if path.endswith("/stats/contributors"):
            return _StubResponse(200, stats_payload)
        return _StubResponse(200, [])

    monkeypatch.setattr(community, "_gh", _gh)

    sig = community.collect("acme", "widget", stars=10, pushed_at=datetime.now(UTC))
    # Five distinct contributors from /stats — fallback would only give 2.
    assert sig.contributors_last_365d == 5


def test_contributors_retries_on_202_then_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    commits = _fake_commits(["alice", "bob", "alice", None])
    stats_calls: list[int] = []

    def _gh(path: str, params: dict | None = None) -> _StubResponse:
        if path.endswith("/commits"):
            return _StubResponse(200, commits)
        if path.endswith("/stats/contributors"):
            stats_calls.append(1)
            return _StubResponse(202, None)
        return _StubResponse(200, [])

    monkeypatch.setattr(community, "_gh", _gh)

    sig = community.collect("acme", "widget", stars=10, pushed_at=datetime.now(UTC))

    # Retried 3 times before giving up — the bug we just fixed.
    assert len(stats_calls) == 3
    # Fallback gives alice + bob + the anonymous email-tagged author.
    assert sig.contributors_last_365d == 3


def test_contributors_empty_stats_payload_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    # GitHub sometimes returns 200 with an empty list while it computes.
    commits = _fake_commits(["alice", "bob", "carol"])

    def _gh(path: str, params: dict | None = None) -> _StubResponse:
        if path.endswith("/commits"):
            return _StubResponse(200, commits)
        if path.endswith("/stats/contributors"):
            return _StubResponse(200, [])
        return _StubResponse(200, [])

    monkeypatch.setattr(community, "_gh", _gh)

    sig = community.collect("acme", "widget", stars=10, pushed_at=datetime.now(UTC))
    assert sig.contributors_last_365d == 3


def test_contributors_zero_when_no_commits_no_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    def _gh(path: str, params: dict | None = None) -> _StubResponse:
        if path.endswith("/commits"):
            return _StubResponse(200, [])
        if path.endswith("/stats/contributors"):
            return _StubResponse(202, None)
        return _StubResponse(200, [])

    monkeypatch.setattr(community, "_gh", _gh)

    sig = community.collect("acme", "widget", stars=10, pushed_at=datetime.now(UTC))
    # No data at all → genuinely 0, not an error.
    assert sig.contributors_last_365d == 0


def test_contributors_network_error_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    commits = _fake_commits(["alice"])

    def _gh(path: str, params: dict | None = None) -> _StubResponse:
        if path.endswith("/commits"):
            return _StubResponse(200, commits)
        if path.endswith("/stats/contributors"):
            raise httpx.ConnectError("boom")
        return _StubResponse(200, [])

    monkeypatch.setattr(community, "_gh", _gh)

    sig = community.collect("acme", "widget", stars=10, pushed_at=datetime.now(UTC))
    # Network error still triggers the commit-author fallback.
    assert sig.contributors_last_365d == 1
