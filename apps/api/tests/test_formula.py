"""Tests for the formula. These are the canonical examples — if the formula
changes, the values here must be updated in lockstep with the docs/spec files.
"""

import pytest

from stackhealth.formula.v1 import (
    FORMULA_VERSION,
    LetterGrade,
    grade_from_score,
    overall,
    security_score,
)


def test_formula_version() -> None:
    assert FORMULA_VERSION == "v1.0"


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, LetterGrade.A_PLUS),
        (95, LetterGrade.A_PLUS),
        (94, LetterGrade.A),
        (90, LetterGrade.A),
        (89, LetterGrade.A_MINUS),
        (70, LetterGrade.B_MINUS),
        (60, LetterGrade.C),
        (49, LetterGrade.F),
        (0, LetterGrade.F),
    ],
)
def test_grade_thresholds(score: int, expected: LetterGrade) -> None:
    assert grade_from_score(score) is expected


def test_overall_express_example() -> None:
    """The worked example from docs/03-SCORING-METHODOLOGY.md.

    security=82, quality=78, hygiene=91, community=89 -> 85 -> A-
    """
    score, grade = overall(security=82, quality=78, hygiene=91, community=89)
    assert score == 85
    assert grade is LetterGrade.A_MINUS


def test_security_score_combines_inputs() -> None:
    s = security_score(scorecard_0_10=8.5, semgrep_0_100=91, dependency_0_100=62)
    # 0.40*85 + 0.40*91 + 0.20*62 = 34 + 36.4 + 12.4 = 82.8 -> 83
    assert s == 83
