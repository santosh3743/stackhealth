"""Outbound notifications. Currently just scan-complete email via Resend.

Templates live in `notify_templates.py`. This module is the transport
layer: it composes a payload and either calls Resend or logs the email
body when `RESEND_API_KEY` isn't set (so dev/local works without signup).
"""

import logging
from datetime import datetime

import httpx

from stackhealth import notify_templates
from stackhealth.config import settings

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"


def _report_link(owner: str, name: str, scan_id: str) -> str:
    base = settings.public_site_url.rstrip("/")
    return f"{base}/r/{owner}/{name}/{scan_id}"


def _methodology_link() -> str:
    return f"{settings.public_site_url.rstrip('/')}/methodology"


def send_scan_complete(
    *,
    to_email: str,
    owner: str,
    name: str,
    scan_id: str,
    overall: int,
    grade: str,
    partial: bool,
    scores: dict[str, int] | None = None,
    language: str | None = None,
    stars: int | None = None,
) -> None:
    """Send (or log) a scan-complete notification.

    Idempotency: caller invokes this once per scan completion (after
    persistence succeeds). If the send fails we log and swallow — never
    fail the worker job because of an email problem.
    """
    report_link = _report_link(owner, name, scan_id)
    methodology_link = _methodology_link()

    subject = notify_templates.scan_complete_subject(
        owner=owner, name=name, grade=grade, overall=overall
    )
    plain = notify_templates.scan_complete_text(
        owner=owner,
        name=name,
        overall=overall,
        grade=grade,
        partial=partial,
        scores=scores,
        language=language,
        stars=stars,
        report_link=report_link,
        methodology_link=methodology_link,
    )
    html = notify_templates.scan_complete_html(
        owner=owner,
        name=name,
        overall=overall,
        grade=grade,
        partial=partial,
        scores=scores,
        language=language,
        stars=stars,
        report_link=report_link,
        methodology_link=methodology_link,
    )

    if not settings.resend_api_key:
        log.info(
            "RESEND_API_KEY not set — would have emailed %s | subject=%r",
            to_email,
            subject,
        )
        return

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "text": plain,
        "html": html,
        "tags": [
            {"name": "kind", "value": "scan_complete"},
            {"name": "scan_id", "value": scan_id},
        ],
    }
    try:
        r = httpx.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=15.0,
        )
    except httpx.HTTPError as e:
        log.warning("resend POST failed for %s: %s", to_email, e)
        return

    if r.status_code >= 300:
        log.warning(
            "resend rejected email to %s (%s): %s",
            to_email,
            r.status_code,
            r.text[:300],
        )
    else:
        log.info(
            "emailed %s at %s",
            to_email,
            datetime.now().isoformat(timespec="seconds"),
        )
