"""Outbound notifications. Currently just scan-complete email via Resend.

If RESEND_API_KEY is not configured, send_scan_complete() logs the email body
at INFO instead of making a network call — so dev/local always works without
sign-up.

Design notes for the HTML email:
- Table-based layout because Gmail/Outlook strip flex/grid CSS.
- All styles inline (Gmail strips <style> blocks).
- Width capped at 560px; on mobile most clients shrink to viewport.
- Dark-mode support via @media (prefers-color-scheme: dark) plus
  meta tag in <head>. Most clients ignore the @media, so the light-
  mode design must look correct on its own — dark mode is a bonus.
- Letter-grade colour matches the web app's GradeBadge component.
"""

import logging
from datetime import datetime

import httpx

from stackhealth.config import settings

log = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"

# Match GradeBadge component in apps/web/components/grade-badge.tsx
_GRADE_COLOR = {
    "A+": "#10b981",
    "A": "#10b981",
    "A-": "#22c55e",
    "B+": "#22c55e",
    "B": "#84cc16",
    "B-": "#84cc16",
    "C+": "#f59e0b",
    "C": "#f59e0b",
    "C-": "#f59e0b",
    "D": "#ef4444",
    "F": "#be123c",
}


def _report_link(owner: str, name: str, scan_id: str) -> str:
    base = settings.public_site_url.rstrip("/")
    return f"{base}/r/{owner}/{name}/{scan_id}"


def _methodology_link() -> str:
    return f"{settings.public_site_url.rstrip('/')}/methodology"


def _qualitative(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Weak"
    return "Poor"


def _render(
    *,
    owner: str,
    name: str,
    scan_id: str,
    overall: int,
    grade: str,
    partial: bool,
    scores: dict[str, int] | None = None,
    language: str | None = None,
    stars: int | None = None,
) -> tuple[str, str, str]:
    """Returns (subject, plain_text, html)."""
    link = _report_link(owner, name, scan_id)
    grade_color = _GRADE_COLOR.get(grade, "#71717a")

    # Subject keeps the strong signal first so it survives Gmail's truncation.
    subject = f"{owner}/{name} scored {grade} ({overall}/100) — StackHealth"

    # ---- plain text variant (for clients that prefer it / accessibility) ----
    meta_line = " · ".join(s for s in [language, f"{stars:,} ★" if stars else None] if s)
    sub_text = ""
    if scores:
        sub_text = (
            "\n  Security:   {security}\n"
            "  Quality:    {quality}\n"
            "  Hygiene:    {hygiene}\n"
            "  Community:  {community}\n"
        ).format(**scores)

    plain = (
        f"Your StackHealth scan of {owner}/{name} is "
        f"{'partial' if partial else 'complete'}.\n"
        f"{meta_line}\n\n"
        f"  Grade:    {grade}\n"
        f"  Overall:  {overall}/100\n"
        f"{sub_text}\n"
        f"Full report: {link}\n\n"
        f"Methodology: {_methodology_link()}\n\n"
        f"— StackHealth · the open code health benchmark"
    )

    # ---- HTML ----
    meta_html = ""
    parts: list[str] = []
    if language:
        parts.append(language)
    if stars is not None:
        parts.append(f"{stars:,} ★")
    if parts:
        meta_html = (
            '<div style="margin-top:6px;color:#71717a;font-size:13px;'
            f'line-height:1.5">{" &middot; ".join(parts)}</div>'
        )

    partial_html = ""
    if partial:
        partial_html = (
            '<tr><td style="padding:0 32px 8px">'
            '<div style="background:#fef3c7;border:1px solid #fcd34d;'
            "color:#92400e;border-radius:8px;padding:10px 12px;"
            'font-size:12px;line-height:1.5">'
            "<strong>Partial scan.</strong> Some engines were skipped; "
            "affected sub-scores use a neutral default. "
            "Details in the full report."
            "</div></td></tr>"
        )

    subscores_html = ""
    if scores:
        rows = [
            ("Security", scores["security"], "30%"),
            ("Quality", scores["quality"], "25%"),
            ("Hygiene", scores["hygiene"], "25%"),
            ("Community", scores["community"], "20%"),
        ]
        cells = "".join(
            f'<td align="center" '
            f'style="width:25%;padding:14px 8px;border:1px solid #e4e4e7;'
            f'border-radius:8px">'
            f'<div style="font-size:11px;color:#71717a;text-transform:uppercase;'
            f'letter-spacing:0.5px">{label}</div>'
            f'<div style="font-size:24px;font-weight:700;color:#18181b;'
            f'margin-top:4px;line-height:1">{value}</div>'
            f'<div style="font-size:11px;color:#a1a1aa;margin-top:2px">'
            f"weight {weight}</div>"
            f"</td>"
            for label, value, weight in rows
        )
        subscores_html = (
            f'<tr><td style="padding:8px 32px 24px">'
            f'<table role="presentation" cellspacing="8" cellpadding="0" '
            f'style="width:100%;border-collapse:separate">'
            f"<tr>{cells}</tr>"
            f"</table></td></tr>"
        )

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="supported-color-schemes" content="light dark">
<title>{owner}/{name} — {grade}</title>
</head>
<body style="margin:0;padding:0;background:#f4f4f5;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,
Helvetica,Arial,sans-serif;color:#18181b">
<div style="display:none;font-size:0;line-height:0;color:transparent;
overflow:hidden;visibility:hidden;mso-hide:all">
{owner}/{name} scored {grade} ({overall}/100) — view the full report.
</div>

<table role="presentation" cellspacing="0" cellpadding="0" border="0"
style="width:100%;background:#f4f4f5">
<tr><td align="center" style="padding:32px 16px">

  <table role="presentation" cellspacing="0" cellpadding="0" border="0"
  style="width:100%;max-width:560px;background:#ffffff;border:1px solid #e4e4e7;
  border-radius:16px;overflow:hidden">

    <!-- Header bar -->
    <tr><td style="padding:20px 32px;border-bottom:1px solid #f4f4f5">
      <table role="presentation" width="100%"><tr>
        <td align="left" style="font-size:16px;font-weight:600;
        letter-spacing:-0.01em;color:#18181b">
          Stack<span style="color:#4f46e5">Health</span>
        </td>
        <td align="right" style="font-size:11px;color:#a1a1aa;
        text-transform:uppercase;letter-spacing:0.5px">
          scan complete
        </td>
      </tr></table>
    </td></tr>

    <!-- Repo title -->
    <tr><td style="padding:28px 32px 12px">
      <div style="font-size:22px;font-weight:700;letter-spacing:-0.01em;
      color:#18181b;line-height:1.25">{owner}/{name}</div>
      {meta_html}
    </td></tr>

    <!-- Hero: grade + score -->
    <tr><td style="padding:8px 32px 12px">
      <table role="presentation" width="100%"><tr>
        <td valign="middle" style="width:96px;padding-right:16px">
          <table role="presentation" cellspacing="0" cellpadding="0" border="0">
            <tr><td align="center" valign="middle"
            style="width:88px;height:88px;background:{grade_color};
            border-radius:50%;color:#ffffff;font-size:32px;font-weight:800;
            line-height:88px;letter-spacing:-0.02em">{grade}</td></tr>
          </table>
        </td>
        <td valign="middle">
          <div style="font-size:48px;font-weight:800;color:#18181b;line-height:1;
          letter-spacing:-0.03em">
            {overall}
            <span style="font-size:18px;font-weight:500;color:#a1a1aa;
            letter-spacing:0">/ 100</span>
          </div>
          <div style="margin-top:6px;font-size:13px;color:#52525b">
            {_qualitative(overall)} overall
          </div>
        </td>
      </tr></table>
    </td></tr>

    {partial_html}

    {subscores_html}

    <!-- CTA button -->
    <tr><td style="padding:8px 32px 28px" align="center">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0">
        <tr><td style="border-radius:10px;background:#4f46e5">
          <a href="{link}" style="display:inline-block;padding:12px 24px;
          font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;
          border-radius:10px">View full report &nbsp;→</a>
        </td></tr>
      </table>
      <div style="margin-top:10px;font-size:11px;color:#a1a1aa;
      word-break:break-all">
        Or copy this URL: {link}
      </div>
    </td></tr>

    <!-- Footer -->
    <tr><td style="padding:18px 32px;border-top:1px solid #f4f4f5;
    background:#fafafa;font-size:11px;color:#71717a;line-height:1.6">
      <strong style="color:#52525b">StackHealth</strong> &mdash; the open
      code health benchmark.<br>
      Every weight, threshold, and penalty is documented at
      <a href="{_methodology_link()}" style="color:#4f46e5;
      text-decoration:none">stackhealth.dev/methodology</a>.<br>
      You received this because you subscribed when submitting this scan.
    </td></tr>

  </table>

</td></tr>
</table>

</body>
</html>"""

    return subject, plain, html


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

    Idempotency: caller invokes this once per scan completion (after persist
    succeeds). If sending fails we log and swallow — never fail the job
    because of an email problem.
    """
    subject, plain, html = _render(
        owner=owner,
        name=name,
        scan_id=scan_id,
        overall=overall,
        grade=grade,
        partial=partial,
        scores=scores,
        language=language,
        stars=stars,
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
