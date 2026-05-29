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


# ─────────────────── monorepo tests_dir discovery ───────────────────


def test_tests_dir_found_in_apps_subdirectory(tmp_path: Path) -> None:
    """A monorepo with tests at apps/api/tests/ should still pass."""
    (tmp_path / "apps" / "api" / "tests").mkdir(parents=True)
    assert hygiene._tests_dir(tmp_path) is True


def test_tests_dir_found_in_packages(tmp_path: Path) -> None:
    (tmp_path / "packages" / "core" / "spec").mkdir(parents=True)
    assert hygiene._tests_dir(tmp_path) is True


def test_tests_dir_found_in_services(tmp_path: Path) -> None:
    (tmp_path / "services" / "auth" / "__tests__").mkdir(parents=True)
    assert hygiene._tests_dir(tmp_path) is True


def test_tests_dir_root_still_works(tmp_path: Path) -> None:
    """Root-level tests/ — the original common case — must still pass."""
    (tmp_path / "tests").mkdir()
    assert hygiene._tests_dir(tmp_path) is True


def test_tests_dir_not_found_when_only_deeper(tmp_path: Path) -> None:
    """Stop at depth 2 — we don't recursively follow into nested workspaces.

    Going arbitrarily deep would invite false positives from vendored
    dependencies (e.g. node_modules/some-pkg/tests/).
    """
    (tmp_path / "apps" / "api" / "src" / "deep" / "tests").mkdir(parents=True)
    assert hygiene._tests_dir(tmp_path) is False


# ─────────────────── LICENSE body sniffing ───────────────────


_MIT_BODY = """\
MIT License

Copyright (c) 2026 Santosh Jha

You are welcome to use, study, modify, and redistribute this software,
including for commercial purposes, provided that you keep the copyright
notice and this license text intact in any copy or substantial portion of
the software. Attribution to Santosh Jha as the original author must be
preserved.

---

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction…
"""

_APACHE_BODY = """\
Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION
"""

_BSD3_BODY = """\
Copyright 2026 Foo

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice…
* Redistributions in binary form must reproduce…
* Neither the name of the copyright holder nor the names of its contributors…
"""

_BSD2_BODY = """\
Copyright 2026 Foo

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice…
2. Redistributions in binary form must reproduce…
"""


@pytest.mark.parametrize(
    ("filename", "body", "expected"),
    [
        ("LICENSE", _MIT_BODY, "MIT"),
        ("LICENSE.md", _MIT_BODY, "MIT"),
        ("LICENSE.txt", _APACHE_BODY, "Apache-2.0"),
        ("COPYING", _BSD3_BODY, "BSD-3-Clause"),
        ("LICENSE", _BSD2_BODY, "BSD-2-Clause"),
    ],
)
def test_detect_spdx_from_known_licenses(
    tmp_path: Path, filename: str, body: str, expected: str
) -> None:
    (tmp_path / filename).write_text(body)
    assert hygiene._detect_spdx_from_license_file(tmp_path) == expected


def test_detect_spdx_no_license_file(tmp_path: Path) -> None:
    assert hygiene._detect_spdx_from_license_file(tmp_path) is None


def test_detect_spdx_unrecognised_text(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("This is some custom proprietary license.\n")
    assert hygiene._detect_spdx_from_license_file(tmp_path) is None


def test_resolve_prefers_github_when_clean(tmp_path: Path) -> None:
    """When GitHub provided a real SPDX, we don't second-guess it."""
    (tmp_path / "LICENSE").write_text(_APACHE_BODY)  # body says Apache
    # GitHub says MIT — we trust it. (Pathological example to assert priority.)
    assert hygiene._resolve_license_spdx(tmp_path, "MIT") == "MIT"


def test_resolve_falls_back_when_github_says_noassertion(tmp_path: Path) -> None:
    """Custom preamble → GitHub returns NOASSERTION → we sniff the body."""
    (tmp_path / "LICENSE").write_text(_MIT_BODY)
    assert hygiene._resolve_license_spdx(tmp_path, "NOASSERTION") == "MIT"


def test_resolve_falls_back_when_github_returns_none(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text(_APACHE_BODY)
    assert hygiene._resolve_license_spdx(tmp_path, None) == "Apache-2.0"


def test_evaluate_credits_license_osi_via_body_sniffing(tmp_path: Path) -> None:
    """End-to-end: an augmented MIT LICENSE with NOASSERTION from GitHub
    should still earn the license_osi points.
    """
    (tmp_path / "LICENSE").write_text(_MIT_BODY)
    result = hygiene.evaluate(
        tmp_path,
        license_spdx="NOASSERTION",
        has_description=False,
        has_topics=False,
        days_since_last_commit=None,
    )
    assert result.breakdown["license_file"] == 15
    assert result.breakdown["license_osi"] == 5  # this was 0 before the fix
