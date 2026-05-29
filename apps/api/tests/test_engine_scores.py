"""Pure-function tests for every engine's score() function.

These deliberately don't shell out to any binary — they hit only the
scoring math. Each engine's "find issues then score them" pipeline is
also covered by its parser tests where applicable.
"""

import pytest

from stackhealth.engines import (
    cloc,
    community,
    complexity,
    duplication,
    lint,
    semgrep,
    trivy,
)

# ─────────────────────────── semgrep ───────────────────────────


def test_semgrep_score_clean_repo() -> None:
    """No findings → full 100."""
    assert semgrep.semgrep_score(errors=0, warnings=0, info=0, loc=10_000) == 100


def test_semgrep_score_loc_normalised() -> None:
    """Same count of findings: bigger repo should score higher."""
    small = semgrep.semgrep_score(errors=5, warnings=10, info=20, loc=1_000)
    large = semgrep.semgrep_score(errors=5, warnings=10, info=20, loc=100_000)
    assert large > small


def test_semgrep_score_severity_weighting() -> None:
    """One ERROR penalises more than one WARNING penalises more than one INFO.

    Uses a small LoC so penalties don't all round to 100.
    """
    err = semgrep.semgrep_score(errors=1, warnings=0, info=0, loc=1_000)
    warn = semgrep.semgrep_score(errors=0, warnings=1, info=0, loc=1_000)
    inf = semgrep.semgrep_score(errors=0, warnings=0, info=1, loc=1_000)
    assert err < warn <= inf


def test_semgrep_score_floor_zero() -> None:
    assert semgrep.semgrep_score(errors=10_000, warnings=0, info=0, loc=100) == 0


# ─────────────────────────── trivy ───────────────────────────


@pytest.mark.parametrize(
    ("critical", "high", "medium", "low", "expected"),
    [
        (0, 0, 0, 0, 100),
        (1, 0, 0, 0, 80),  # 20 penalty
        (0, 1, 0, 0, 92),  # 8 penalty
        (0, 0, 1, 0, 97),  # 3 penalty
        (0, 0, 0, 1, 99),  # 1 penalty
        (5, 0, 0, 0, 0),  # 100 penalty, clamped
    ],
)
def test_trivy_dependency_score(critical, high, medium, low, expected) -> None:
    assert trivy.dependency_score(critical=critical, high=high, medium=medium, low=low) == expected


# ─────────────────────────── complexity (lizard) ───────────────────────────


@pytest.mark.parametrize(
    ("avg", "expected"),
    [
        (1.0, 100),
        (3.0, 100),
        (5.0, 100),  # threshold
        (6.0, 92),  # 8pt drop per point above 5
        (7.0, 84),
        (15.0, 20),
        (20.0, 0),  # floor
    ],
)
def test_complexity_score(avg, expected) -> None:
    assert complexity.complexity_score(avg) == expected


# ─────────────────────────── duplication (jscpd) ───────────────────────────


@pytest.mark.parametrize(
    ("pct", "expected"),
    [
        (0.0, 100),
        (5.0, 75),
        (10.0, 50),
        (20.0, 0),
        (50.0, 0),  # floor
    ],
)
def test_duplication_score(pct, expected) -> None:
    assert duplication.duplication_score(pct) == expected


# ─────────────────────────── cloc (file size) ───────────────────────────


@pytest.mark.parametrize(
    ("mega_files", "expected"),
    [
        (0, 100),
        (5, 75),  # 5 pt per mega-file
        (20, 0),
        (100, 0),  # floor
    ],
)
def test_file_size_score(mega_files, expected) -> None:
    assert cloc.file_size_score(mega_files) == expected


# ─────────────────────────── lint density ───────────────────────────


def test_lint_density_no_loc_returns_max() -> None:
    """A repo with zero LoC has nothing to lint — don't divide by zero."""
    assert lint.lint_density_score(total_issues=0, loc=0) == 100
    assert lint.lint_density_score(total_issues=100, loc=0) == 100


def test_lint_density_clean_repo() -> None:
    assert lint.lint_density_score(total_issues=0, loc=10_000) == 100


def test_lint_density_penalty() -> None:
    """Each issue/kLoC costs 2 points."""
    # 10 issues / 5 kLoC = 2 issues/kLoC → 4 pt penalty
    assert lint.lint_density_score(total_issues=10, loc=5_000) == 96


def test_lint_density_floor() -> None:
    assert lint.lint_density_score(total_issues=1_000_000, loc=1_000) == 0


# ─────────────────────────── community ───────────────────────────


def test_activity_score_dormant() -> None:
    assert community.activity_score(days_since_last_commit=400, commits_last_90d=0) == 0


def test_activity_score_stale_but_alive() -> None:
    assert community.activity_score(days_since_last_commit=200, commits_last_90d=0) == 30


def test_activity_score_active() -> None:
    # 40 base + 2 * commits, capped at 100
    assert community.activity_score(days_since_last_commit=10, commits_last_90d=0) == 40
    assert community.activity_score(days_since_last_commit=10, commits_last_90d=20) == 80
    assert community.activity_score(days_since_last_commit=10, commits_last_90d=100) == 100


def test_activity_score_no_pushed_at() -> None:
    assert community.activity_score(days_since_last_commit=None, commits_last_90d=99) == 0


def test_contributor_score_log_curve() -> None:
    """log2(n+1) * 25, cap 100. Doubling contributors adds ~25 points."""
    assert community.contributor_score(0) == 0
    assert community.contributor_score(1) == 25
    assert community.contributor_score(3) == 50
    assert community.contributor_score(7) == 75
    assert community.contributor_score(15) == 100
    assert community.contributor_score(1_000) == 100  # cap


def test_popularity_score_log10() -> None:
    """log10(n+1) * 25, cap 100. A 10x increase in stars adds 25 points."""
    assert community.popularity_score(0) == 0
    assert community.popularity_score(9) == 25
    assert community.popularity_score(99) == 50
    assert community.popularity_score(999) == 75
    assert community.popularity_score(10_000) == 100
    assert community.popularity_score(1_000_000) == 100  # cap


def test_responsiveness_score_buckets() -> None:
    assert community.responsiveness_score(median_hours=10, issues_in_90d=5) == 100
    assert community.responsiveness_score(median_hours=48, issues_in_90d=5) == 80
    assert community.responsiveness_score(median_hours=100, issues_in_90d=5) == 60
    assert community.responsiveness_score(median_hours=200, issues_in_90d=5) == 30
    assert community.responsiveness_score(median_hours=2_000, issues_in_90d=5) == 0


def test_responsiveness_no_issues_is_neutral() -> None:
    """Repos with no issues in 90 days get a neutral 70 — not penalised."""
    assert community.responsiveness_score(median_hours=None, issues_in_90d=0) == 70


def test_responsiveness_unknown_median_with_issues() -> None:
    """Has issues but we couldn't compute a median: middling 60."""
    assert community.responsiveness_score(median_hours=None, issues_in_90d=5) == 60
