"""GET /r/:owner/:name/badge.svg — embeddable badge.

TODO (Week 4): proper SVG generation per docs/10-FRONTEND-PAGES.md.
For now returns a stub that proves the route works.
"""
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
    "A+": "#10b981", "A": "#10b981", "A-": "#22c55e",
    "B+": "#22c55e", "B": "#84cc16", "B-": "#84cc16",
    "C+": "#f59e0b", "C": "#f59e0b", "C-": "#f59e0b",
    "D": "#ef4444",
    "F": "#be123c",
}


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
