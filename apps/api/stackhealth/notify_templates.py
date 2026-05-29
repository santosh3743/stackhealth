"""Email body templates. Kept separate from `notify.py` so that:

- The HTML can be inspected / iterated visually without touching send logic.
- Unit tests can render templates without touching httpx.
- Future templates (weekly digest, badge-published-elsewhere, …) live here too.

Email-safety rules these templates follow (and any new one must):
- Table-based layout (Gmail and Outlook strip flex/grid CSS).
- All styles inline (Gmail strips <style> blocks).
- Width capped at 560px; mobile clients shrink to viewport.
- Light-mode design must be correct on its own — dark mode is bonus.
"""

# Match GradeBadge component in apps/web/components/grade-badge.tsx.
GRADE_COLOR = {
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


def qualitative_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Weak"
    return "Poor"


def scan_complete_subject(*, owner: str, name: str, grade: str, overall: int) -> str:
    """Keeps the strong signal first so it survives Gmail's subject truncation."""
    return f"{owner}/{name} scored {grade} ({overall}/100) — StackHealth"


def scan_complete_text(
    *,
    owner: str,
    name: str,
    overall: int,
    grade: str,
    partial: bool,
    scores: dict[str, int] | None,
    language: str | None,
    stars: int | None,
    report_link: str,
    methodology_link: str,
) -> str:
    """Plain-text variant (for clients that prefer it / accessibility)."""
    meta_line = " · ".join(s for s in [language, f"{stars:,} ★" if stars else None] if s)
    sub_text = ""
    if scores:
        sub_text = (
            "\n  Security:   {security}\n"
            "  Quality:    {quality}\n"
            "  Hygiene:    {hygiene}\n"
            "  Community:  {community}\n"
        ).format(**scores)
    return (
        f"Your StackHealth scan of {owner}/{name} is "
        f"{'partial' if partial else 'complete'}.\n"
        f"{meta_line}\n\n"
        f"  Grade:    {grade}\n"
        f"  Overall:  {overall}/100\n"
        f"{sub_text}\n"
        f"Full report: {report_link}\n\n"
        f"Methodology: {methodology_link}\n\n"
        f"— StackHealth · the open code health benchmark"
    )


def scan_complete_html(
    *,
    owner: str,
    name: str,
    overall: int,
    grade: str,
    partial: bool,
    scores: dict[str, int] | None,
    language: str | None,
    stars: int | None,
    report_link: str,
    methodology_link: str,
) -> str:
    """Branded HTML email matching the web app's visual language."""
    grade_color = GRADE_COLOR.get(grade, "#71717a")

    parts: list[str] = []
    if language:
        parts.append(language)
    if stars is not None:
        parts.append(f"{stars:,} ★")
    meta_html = (
        (
            '<div style="margin-top:6px;color:#71717a;font-size:13px;'
            f'line-height:1.5">{" &middot; ".join(parts)}</div>'
        )
        if parts
        else ""
    )

    partial_html = (
        (
            '<tr><td style="padding:0 32px 8px">'
            '<div style="background:#fef3c7;border:1px solid #fcd34d;'
            "color:#92400e;border-radius:8px;padding:10px 12px;"
            'font-size:12px;line-height:1.5">'
            "<strong>Partial scan.</strong> Some engines were skipped; "
            "affected sub-scores use a neutral default. "
            "Details in the full report."
            "</div></td></tr>"
        )
        if partial
        else ""
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

    return f"""\
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

    <tr><td style="padding:28px 32px 12px">
      <div style="font-size:22px;font-weight:700;letter-spacing:-0.01em;
      color:#18181b;line-height:1.25">{owner}/{name}</div>
      {meta_html}
    </td></tr>

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
            {qualitative_label(overall)} overall
          </div>
        </td>
      </tr></table>
    </td></tr>

    {partial_html}

    {subscores_html}

    <tr><td style="padding:8px 32px 28px" align="center">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0">
        <tr><td style="border-radius:10px;background:#4f46e5">
          <a href="{report_link}" style="display:inline-block;padding:12px 24px;
          font-size:14px;font-weight:600;color:#ffffff;text-decoration:none;
          border-radius:10px">View full report &nbsp;→</a>
        </td></tr>
      </table>
      <div style="margin-top:10px;font-size:11px;color:#a1a1aa;
      word-break:break-all">
        Or copy this URL: {report_link}
      </div>
    </td></tr>

    <tr><td style="padding:18px 32px;border-top:1px solid #f4f4f5;
    background:#fafafa;font-size:11px;color:#71717a;line-height:1.6">
      <strong style="color:#52525b">StackHealth</strong> &mdash; the open
      code health benchmark.<br>
      Every weight, threshold, and penalty is documented at
      <a href="{methodology_link}" style="color:#4f46e5;
      text-decoration:none">stackhealth.dev/methodology</a>.<br>
      You received this because you subscribed when submitting this scan.
    </td></tr>

  </table>

</td></tr>
</table>

</body>
</html>"""
