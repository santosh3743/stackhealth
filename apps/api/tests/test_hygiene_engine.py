"""Hygiene engine — touches a real filesystem (tmp_path) but no network."""

from pathlib import Path

import pytest

from stackhealth.engines import hygiene


@pytest.fixture
def empty_repo(tmp_path: Path) -> Path:
    """A repo with literally nothing in it."""
    return tmp_path


@pytest.fixture
def well_maintained_repo(tmp_path: Path) -> Path:
    """A repo that hits every hygiene check."""
    (tmp_path / "README.md").write_text("# project\n\n" + ("a" * 400))
    (tmp_path / "LICENSE").write_text("MIT License\n")
    (tmp_path / "CONTRIBUTING.md").write_text("see CONTRIBUTING\n")
    (tmp_path / "CODE_OF_CONDUCT.md").write_text("be nice\n")
    (tmp_path / "SECURITY.md").write_text("report\n")
    (tmp_path / ".gitignore").write_text("__pycache__\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text("def test_x(): pass\n")

    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        "name: ci\non:\n  pull_request:\n    branches: [main]\njobs:\n  test:\n"
        "    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n"
    )
    return tmp_path


def test_empty_repo_scores_zero_except_recent_commit(empty_repo: Path) -> None:
    result = hygiene.evaluate(
        empty_repo,
        license_spdx=None,
        has_description=False,
        has_topics=False,
        days_since_last_commit=None,
    )
    # Every check should fail.
    assert result.score == 0
    for key, points in result.breakdown.items():
        assert points == 0, f"{key} unexpectedly scored {points} on an empty repo"


def test_well_maintained_repo_hits_close_to_100(well_maintained_repo: Path) -> None:
    result = hygiene.evaluate(
        well_maintained_repo,
        license_spdx="MIT",
        has_description=True,
        has_topics=True,
        days_since_last_commit=10,
    )
    # MIT is OSI-approved → license_osi=5; recent push → 7; description → 5;
    # topics → 5; everything else → its max. Should be very close to 100.
    assert result.score >= 95, result.breakdown
    assert result.breakdown["readme"] == 15
    assert result.breakdown["license_osi"] == 5
    assert result.breakdown["ci_pr_trigger"] == 5
    assert result.breakdown["tests_dir"] == 10


def test_non_osi_license_loses_5_points(well_maintained_repo: Path) -> None:
    result = hygiene.evaluate(
        well_maintained_repo,
        license_spdx="Some-Custom-License",
        has_description=True,
        has_topics=True,
        days_since_last_commit=10,
    )
    assert result.breakdown["license_file"] == 15  # file exists
    assert result.breakdown["license_osi"] == 0  # but it's not OSI-approved


def test_stale_repo_loses_recent_commit_points(well_maintained_repo: Path) -> None:
    result = hygiene.evaluate(
        well_maintained_repo,
        license_spdx="MIT",
        has_description=True,
        has_topics=True,
        days_since_last_commit=400,  # >365
    )
    assert result.breakdown["recent_commit"] == 0


def test_short_readme_doesnt_qualify(empty_repo: Path) -> None:
    (empty_repo / "README.md").write_text("# x")  # well under 300 chars
    result = hygiene.evaluate(
        empty_repo,
        license_spdx=None,
        has_description=False,
        has_topics=False,
        days_since_last_commit=None,
    )
    assert result.breakdown["readme"] == 0
