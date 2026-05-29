"""Pydantic boundary tests — these are the cheapest, highest-leverage tests
because every malformed request would otherwise have to be caught at runtime.
"""

import pytest
from pydantic import ValidationError

from stackhealth.schemas import ScanCreate
from stackhealth.schemas.scan import ScanNotifyUpdate

# Every ScanCreate needs an email — these URL-parsing tests pass this
# valid-looking dummy and assert on URL handling separately.
_VALID_EMAIL = "test@example.com"

# ─────────────────────────── repo URL parsing ───────────────────────────


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/pallets/click",
        "https://github.com/pallets/click/",
        "https://github.com/pallets/click.git",
        "http://github.com/pallets/click",
        "https://GitHub.com/PALLETS/Click",
        "https://github.com/some-user/some.repo",
        "https://github.com/A_underscore/dashed-name",
    ],
)
def test_valid_github_urls(url: str) -> None:
    payload = ScanCreate(repo_url=url, notify_email=_VALID_EMAIL)
    owner, name = payload.owner_and_name
    assert owner and name


@pytest.mark.parametrize(
    "url",
    [
        "https://gitlab.com/foo/bar",
        "https://bitbucket.org/foo/bar",
        "not a url at all",
        "https://github.com/foo",  # missing repo
        "https://github.com/",  # missing both
        "https://github.com/foo/bar/baz",  # too many segments
        "ftp://github.com/foo/bar",
    ],
)
def test_invalid_urls_rejected(url: str) -> None:
    with pytest.raises(ValidationError):
        ScanCreate(repo_url=url, notify_email=_VALID_EMAIL)


def test_owner_and_name_extraction() -> None:
    payload = ScanCreate(
        repo_url="https://github.com/Pallets/Click.git",
        notify_email=_VALID_EMAIL,
    )
    owner, name = payload.owner_and_name
    assert owner == "Pallets"
    assert name == "Click"  # `.git` stripped


# ─────────────────────────── notify email ───────────────────────────


def test_notify_email_is_required_on_create() -> None:
    """Email is mandatory — every scan must have a notification target."""
    with pytest.raises(ValidationError):
        ScanCreate(repo_url="https://github.com/foo/bar")  # type: ignore[call-arg]


def test_notify_email_validates_format() -> None:
    with pytest.raises(ValidationError):
        ScanCreate(repo_url="https://github.com/foo/bar", notify_email="not-an-email")


def test_notify_email_accepts_valid() -> None:
    payload = ScanCreate(
        repo_url="https://github.com/foo/bar",
        notify_email="user@example.com",
    )
    assert payload.notify_email == "user@example.com"


def test_notify_update_can_clear_email() -> None:
    """Passing null is the documented opt-out path."""
    payload = ScanNotifyUpdate(notify_email=None)
    assert payload.notify_email is None


def test_notify_update_validates_email() -> None:
    with pytest.raises(ValidationError):
        ScanNotifyUpdate(notify_email="no-at-sign")
