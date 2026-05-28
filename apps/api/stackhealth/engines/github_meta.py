"""Fetch repo metadata from the GitHub REST API.

Used both at scan submission (to verify the repo is public) and during the
scan (to populate stars, language, license, contributor count, etc.).
"""
from dataclasses import dataclass
from datetime import datetime

import httpx

from stackhealth.config import settings


class GitHubError(RuntimeError):
    pass


@dataclass(frozen=True)
class RepoMeta:
    owner: str
    name: str
    description: str | None
    homepage: str | None
    default_branch: str
    language: str | None
    stars: int
    forks: int
    license_spdx: str | None
    is_archived: bool
    is_fork: bool
    is_private: bool
    pushed_at: datetime | None
    topics: tuple[str, ...] = ()
    clone_url: str = ""


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        h["Authorization"] = f"Bearer {settings.github_token}"
    return h


def fetch_repo(owner: str, name: str) -> RepoMeta:
    url = f"https://api.github.com/repos/{owner}/{name}"
    r = httpx.get(url, headers=_headers(), timeout=10.0, follow_redirects=True)
    if r.status_code == 404:
        raise GitHubError("repo_not_found")
    if r.status_code == 403:
        raise GitHubError("rate_limited")
    r.raise_for_status()
    data = r.json()

    return RepoMeta(
        owner=data["owner"]["login"],
        name=data["name"],
        description=data.get("description"),
        homepage=data.get("homepage"),
        default_branch=data["default_branch"],
        language=data.get("language"),
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        license_spdx=(data.get("license") or {}).get("spdx_id"),
        is_archived=data["archived"],
        is_fork=data["fork"],
        is_private=data["private"],
        pushed_at=datetime.fromisoformat(data["pushed_at"].replace("Z", "+00:00"))
        if data.get("pushed_at") else None,
        topics=tuple(data.get("topics") or ()),
        clone_url=data.get("clone_url") or f"https://github.com/{owner}/{name}.git",
    )
