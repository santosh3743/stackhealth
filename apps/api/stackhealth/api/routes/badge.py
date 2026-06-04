"""GET /r/:owner/:name/badge.svg — embeddable badge.
GET /r/:owner/:name/card.svg  — rich scorecard for README embedding.

Both endpoints serve the latest *complete* scan for the repo. The badge
is the classic shields.io-style strip; the card is a self-contained
scorecard with overall grade + sub-dimensions, sized for README display
(440 x 220 px).
"""

from datetime import UTC, datetime
from html import escape

from fastapi import APIRouter, Depends, Response
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from stackhealth.api.deps import get_db
from stackhealth.models import Repo, Scan
from stackhealth.models.scan import ScanStatus

router = APIRouter()

CACHE_SECONDS = 3600


def _svg(label: str, value: str, color: str) -> str:
    # Minimal flat badge. Replace with real generator in Week 4.
    label_width = max(60, len(label) * 7)
    value_width = max(40, len(value) * 9)
    total = label_width + value_width
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{total}" height="20">
  <rect width="{label_width}" height="20" fill="#555"/>
  <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width // 2}" y="14">{label}</text>
    <text x="{label_width + value_width // 2}" y="14">{value}</text>
  </g>
</svg>"""


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


CARD_W = 440
CARD_H = 220


def _bar_color(value: int) -> str:
    if value >= 80:
        return "#10b981"
    if value >= 60:
        return "#22c55e"
    if value >= 40:
        return "#f59e0b"
    return "#ef4444"


def _card_svg(
    repo_slug: str,
    grade: str,
    score: int | None,
    grade_color: str,
    scores: dict[str, int | None] | None,
    formula_version: str,
    completed_at: datetime | None,
) -> str:
    # Pure-SVG card — no external fonts, no JS. GitHub README image
    # rendering caches by URL, so the badge route's 1-hour Cache-Control
    # is enough; we don't need to bake the scan_id into the URL.
    score_str = str(score) if score is not None else "—"
    slug = escape(repo_slug)[:42]
    completed = completed_at.astimezone(UTC).strftime("%d %b %Y") if completed_at else "—"
    formula = escape(formula_version)

    dims = scores or {}
    dim_order = [
        ("Security", dims.get("security")),
        ("Quality", dims.get("quality")),
        ("Hygiene", dims.get("hygiene")),
        ("Community", dims.get("community")),
    ]
    bar_x = 150
    bar_w = 200
    rows: list[str] = []
    for i, (label, value) in enumerate(dim_order):
        y = 100 + i * 24
        v = value if isinstance(value, int) else 0
        filled = max(0, min(bar_w, round(bar_w * v / 100)))
        color = _bar_color(v) if value is not None else "#3f3f46"
        value_text = str(value) if value is not None else "—"
        rows.append(
            f'<text x="30" y="{y + 4}" fill="#e4e4e7" font-size="13">{label}</text>'
            f'<rect x="{bar_x}" y="{y - 7}" width="{bar_w}" height="10" rx="5" fill="#27272a"/>'
            f'<rect x="{bar_x}" y="{y - 7}" width="{filled}" height="10" rx="5" fill="{color}"/>'
            f'<text x="{bar_x + bar_w + 10}" y="{y + 4}" fill="#e4e4e7" font-size="13" font-family="ui-monospace, SFMono-Regular, Menlo, monospace">{value_text}</text>'
        )

    rows_svg = "\n  ".join(rows)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{CARD_H}" viewBox="0 0 {CARD_W} {CARD_H}" role="img" aria-label="StackHealth scorecard for {slug}: {grade} {score_str}/100">
  <style>
    .title {{ font: 600 13px ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
    .repo  {{ font: 500 15px ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
    .grade {{ font: 800 44px ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}
    .score {{ font: 700 28px ui-monospace, SFMono-Regular, Menlo, monospace; }}
    .meta  {{ font: 400 11px ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; fill: #71717a; }}
  </style>
  <rect width="{CARD_W}" height="{CARD_H}" rx="14" fill="#09090b"/>
  <rect width="{CARD_W}" height="{CARD_H}" rx="14" fill="none" stroke="#27272a" stroke-width="1"/>

  <!-- header -->
  <text x="30" y="32" class="title" fill="#71717a">STACKHEALTH</text>
  <text x="30" y="56" class="repo"  fill="#fafafa">{slug}</text>

  <!-- grade + score -->
  <text x="30"  y="92" class="grade" fill="{grade_color}">{grade}</text>
  <text x="105" y="88" class="score" fill="#e4e4e7">{score_str}<tspan font-size="14" fill="#71717a"> /100</tspan></text>

  <!-- sub-dimensions -->
  {rows_svg}

  <!-- footer -->
  <text x="30"  y="{CARD_H - 14}" class="meta">Formula {formula} · scanned {completed}</text>
  <text x="{CARD_W - 30}" y="{CARD_H - 14}" class="meta" text-anchor="end">stackhealth.dev</text>
</svg>"""


@router.get("/r/{owner}/{name}/badge.svg")
def badge(owner: str, name: str, db: Session = Depends(get_db)) -> Response:
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    grade = "?"
    color = "#9ca3af"
    if repo is not None:
        scan = db.scalar(
            select(Scan)
            .where(Scan.repo_id == repo.id, Scan.status == ScanStatus.complete)
            .order_by(desc(Scan.completed_at))
            .limit(1)
        )
        if scan and scan.grade:
            grade = scan.grade.value
            color = GRADE_COLOR.get(grade, "#9ca3af")

    svg = _svg("stackhealth", grade, color)
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": f"public, max-age={CACHE_SECONDS}, s-maxage={CACHE_SECONDS}"},
    )


@router.get("/r/{owner}/{name}/card.svg")
def card(owner: str, name: str, db: Session = Depends(get_db)) -> Response:
    """Rich scorecard SVG. Designed for README embedding (440 x 220 px)."""
    repo = db.scalar(select(Repo).where(Repo.owner == owner, Repo.name == name))
    grade = "?"
    color = "#9ca3af"
    score: int | None = None
    scores: dict[str, int | None] | None = None
    completed_at = None
    formula_version = "v1.0"

    if repo is not None:
        scan = db.scalar(
            select(Scan)
            .where(Scan.repo_id == repo.id, Scan.status == ScanStatus.complete)
            .order_by(desc(Scan.completed_at))
            .limit(1)
        )
        if scan is not None:
            if scan.grade:
                grade = scan.grade.value
                color = GRADE_COLOR.get(grade, "#9ca3af")
            score = scan.overall_score
            scores = {
                "security": scan.security_score,
                "quality": scan.quality_score,
                "hygiene": scan.hygiene_score,
                "community": scan.community_score,
            }
            completed_at = scan.completed_at
            formula_version = scan.formula_version

    svg = _card_svg(
        repo_slug=f"{owner}/{name}",
        grade=grade,
        score=score,
        grade_color=color,
        scores=scores,
        formula_version=formula_version,
        completed_at=completed_at,
    )
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": f"public, max-age={CACHE_SECONDS}, s-maxage={CACHE_SECONDS}"},
    )
