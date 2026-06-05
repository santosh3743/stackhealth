"""Disposable email detection.

Loads a bundled list of disposable / throwaway email domains at import
and exposes `is_disposable(email)`. The list lives at
`data/disposable_domains.txt` and can be edited without code changes —
adding a new domain is just a one-line append.
"""

from __future__ import annotations

from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def _disposable_domains() -> frozenset[str]:
    raw = resources.files("stackhealth.data").joinpath("disposable_domains.txt").read_text()
    domains: set[str] = set()
    for line in raw.splitlines():
        line = line.strip().lower()
        if not line or line.startswith("#"):
            continue
        domains.add(line)
    return frozenset(domains)


def is_disposable(email: str) -> bool:
    """True if `email`'s domain (or any parent domain) is on the disposable
    list. Sub-domains of a listed apex match too — `foo.mailinator.com`
    is treated the same as `mailinator.com`.
    """
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].strip().lower()
    if not domain:
        return False
    blocklist = _disposable_domains()
    if domain in blocklist:
        return True
    # Match any parent domain. Cheaper than the alternative (iterating
    # the full blocklist) because most addresses have ≤4 labels.
    parts = domain.split(".")
    for i in range(1, len(parts) - 1):
        if ".".join(parts[i:]) in blocklist:
            return True
    return False
