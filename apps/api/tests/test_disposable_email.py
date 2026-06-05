"""Disposable email detection + schema rejection."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from stackhealth.disposable_email import is_disposable
from stackhealth.schemas.scan import ScanCreate, ScanNotifyUpdate


@pytest.mark.parametrize(
    "email",
    [
        "user@mailinator.com",
        "USER@MAILINATOR.COM",  # case-insensitive
        "user@10minutemail.com",
        "user@guerrillamail.com",
        "user@sharklasers.com",  # guerrillamail family
        "user@yopmail.com",
        "user@temp-mail.org",
        "user@discard.email",
        "user@throwawaymail.com",
        "user@trashmail.de",
        "alice+tag@mailinator.com",  # plus-addressing doesn't help
        "user@sub.mailinator.com",  # subdomains of a listed apex match
    ],
)
def test_is_disposable_true(email: str) -> None:
    assert is_disposable(email) is True


@pytest.mark.parametrize(
    "email",
    [
        "santosh3743@gmail.com",
        "alice@protonmail.com",
        "person@company.co",
        "ops@stackhealth.dev",
        "dev@anthropic.com",
        "user@outlook.com",
        "user@icloud.com",
        # Tricky: a non-disposable that happens to contain a disposable
        # substring should NOT match.
        "user@notmailinator-real.com",
    ],
)
def test_is_disposable_false(email: str) -> None:
    assert is_disposable(email) is False


def test_is_disposable_malformed_input_is_false() -> None:
    # We rely on Pydantic's EmailStr to catch malformed addresses first;
    # the disposable check should never raise.
    assert is_disposable("not-an-email") is False
    assert is_disposable("") is False
    assert is_disposable("@") is False
    assert is_disposable("user@") is False


def test_scan_create_rejects_disposable_email() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScanCreate(
            repo_url="https://github.com/pallets/click",
            notify_email="someone@mailinator.com",
        )
    assert "disposable" in str(exc_info.value).lower()


def test_scan_create_accepts_real_email() -> None:
    payload = ScanCreate(
        repo_url="https://github.com/pallets/click",
        notify_email="santosh3743@gmail.com",
    )
    assert str(payload.notify_email) == "santosh3743@gmail.com"


def test_scan_notify_update_rejects_disposable() -> None:
    with pytest.raises(ValidationError) as exc_info:
        ScanNotifyUpdate(notify_email="someone@guerrillamail.com")
    assert "disposable" in str(exc_info.value).lower()


def test_scan_notify_update_accepts_none() -> None:
    # Setting notify_email=None is how a user opts out; must stay allowed.
    payload = ScanNotifyUpdate(notify_email=None)
    assert payload.notify_email is None
