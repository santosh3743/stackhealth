"""Formula v1.0 — the open scoring formula.

This file is the *executable mirror* of:
    docs/03-SCORING-METHODOLOGY.md
    packages/formula-spec/v1.0.md

KEEP THEM IN SYNC. Any change to weights/thresholds here MUST land in those
two files in the same commit.
"""

from enum import StrEnum

FORMULA_VERSION = "v1.0"

# Top-level dimension weights (sum to 1.0).
W_SECURITY = 0.30
W_QUALITY = 0.25
W_HYGIENE = 0.25
W_COMMUNITY = 0.20

# Security sub-weights (sum to 1.0).
W_SEC_SCORECARD = 0.40
W_SEC_SEMGREP = 0.40
W_SEC_DEPENDENCIES = 0.20

# Quality sub-weights (sum to 1.0).
W_Q_COMPLEXITY = 0.30
W_Q_LINT = 0.25
W_Q_DUPLICATION = 0.20
W_Q_TEST_SIGNAL = 0.15
W_Q_FILE_SIZE = 0.10

# Community sub-weights (sum to 1.0).
W_C_ACTIVITY = 0.35
W_C_CONTRIBUTORS = 0.25
W_C_POPULARITY = 0.20
W_C_RESPONSIVENESS = 0.20


class LetterGrade(StrEnum):
    A_PLUS = "A+"
    A = "A"
    A_MINUS = "A-"
    B_PLUS = "B+"
    B = "B"
    B_MINUS = "B-"
    C_PLUS = "C+"
    C = "C"
    C_MINUS = "C-"
    D = "D"
    F = "F"


_GRADE_THRESHOLDS: tuple[tuple[int, LetterGrade], ...] = (
    (95, LetterGrade.A_PLUS),
    (90, LetterGrade.A),
    (85, LetterGrade.A_MINUS),
    (80, LetterGrade.B_PLUS),
    (75, LetterGrade.B),
    (70, LetterGrade.B_MINUS),
    (65, LetterGrade.C_PLUS),
    (60, LetterGrade.C),
    (55, LetterGrade.C_MINUS),
    (50, LetterGrade.D),
)


def grade_from_score(score: int) -> LetterGrade:
    """Map a 0-100 score to a letter grade (per docs/03-SCORING-METHODOLOGY.md)."""
    if not 0 <= score <= 100:
        raise ValueError(f"score must be 0-100, got {score}")
    for threshold, grade in _GRADE_THRESHOLDS:
        if score >= threshold:
            return grade
    return LetterGrade.F


def _clip(v: float) -> int:
    return max(0, min(100, round(v)))


# --- Sub-score computations ---


def security_score(scorecard_0_10: float, semgrep_0_100: float, dependency_0_100: float) -> int:
    """Per docs/03 §1.

    scorecard_0_10: OpenSSF Scorecard aggregate (0-10)
    semgrep_0_100:  LoC-normalised Semgrep score (0-100)
    dependency_0_100: trivy CVE-penalty score (0-100)
    """
    return _clip(
        W_SEC_SCORECARD * (scorecard_0_10 * 10)
        + W_SEC_SEMGREP * semgrep_0_100
        + W_SEC_DEPENDENCIES * dependency_0_100
    )


def quality_score(
    *,
    complexity: float,
    lint_density: float,
    duplication: float,
    test_signal: float,
    file_size: float,
) -> int:
    """Per docs/03 §2. All inputs 0-100."""
    return _clip(
        W_Q_COMPLEXITY * complexity
        + W_Q_LINT * lint_density
        + W_Q_DUPLICATION * duplication
        + W_Q_TEST_SIGNAL * test_signal
        + W_Q_FILE_SIZE * file_size
    )


def community_score(
    *,
    activity: float,
    contributors: float,
    popularity: float,
    responsiveness: float,
) -> int:
    """Per docs/03 §4. All inputs 0-100."""
    return _clip(
        W_C_ACTIVITY * activity
        + W_C_CONTRIBUTORS * contributors
        + W_C_POPULARITY * popularity
        + W_C_RESPONSIVENESS * responsiveness
    )


def overall(security: int, quality: int, hygiene: int, community: int) -> tuple[int, LetterGrade]:
    """Compute the overall score and letter grade.

    All four inputs are 0-100 sub-scores. Returns (score, grade).
    """
    score = _clip(
        W_SECURITY * security + W_QUALITY * quality + W_HYGIENE * hygiene + W_COMMUNITY * community
    )
    return score, grade_from_score(score)
