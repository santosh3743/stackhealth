"""The open formula — the single source of truth for scoring logic.

`v1.py` MUST stay in sync with:
    - docs/03-SCORING-METHODOLOGY.md (human-readable spec)
    - packages/formula-spec/v1.0.md (frozen spec, published to stackhealth-dev/formula)

If you change one, change all three.
"""
from stackhealth.formula.v1 import (
    FORMULA_VERSION,
    LetterGrade,
    grade_from_score,
    overall,
)

__all__ = ["FORMULA_VERSION", "LetterGrade", "grade_from_score", "overall"]
