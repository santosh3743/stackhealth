"""Tests for the engine registry."""

import pytest

from stackhealth.engines import _registry
from stackhealth.formula.defaults import UNKNOWN_TOOL_VERSION
from stackhealth.models.finding import FindingEngine


def test_registry_is_not_empty() -> None:
    assert len(_registry.REGISTRY) > 0


def test_registry_names_unique() -> None:
    names = [e.name for e in _registry.REGISTRY]
    assert len(names) == len(set(names)), f"duplicate engine names: {names}"


def test_persisted_finding_engines_are_registered() -> None:
    """Every engine that produces persisted findings must be in the registry,
    otherwise we'd lose version-tracking for it.
    """
    finding_engine_names = {e.value for e in FindingEngine}
    registered = {e.name for e in _registry.REGISTRY}
    # `complexity` and `duplication` are tracked via lizard / jscpd binaries.
    # `lint` (FindingEngine member) maps to registered `lint`.
    aliases = {"complexity": "lizard", "duplication": "jscpd"}
    for finding_engine in finding_engine_names:
        expected = aliases.get(finding_engine, finding_engine)
        assert expected in registered, (
            f"FindingEngine.{finding_engine} (registry key '{expected}') "
            f"is not in the engine registry"
        )


def test_get_known_engine() -> None:
    desc = _registry.get("semgrep")
    assert desc.name == "semgrep"
    assert desc.binary == "semgrep"


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        _registry.get("not-a-real-engine")


def test_pure_python_engine_has_no_binary() -> None:
    """Engines without an external binary return UNKNOWN_TOOL_VERSION for version."""
    desc = _registry.get("hygiene")
    assert desc.binary is None
    assert desc.detect_version() == UNKNOWN_TOOL_VERSION


def test_detect_versions_only_includes_binary_engines() -> None:
    """Pure-Python engines aren't included in the tool_versions dict —
    only ones with a real external binary to track.
    """
    versions = _registry.detect_versions({"hygiene", "test_signal", "community"})
    assert versions == {}


def test_detect_versions_skips_unknown_engines() -> None:
    """An unknown name in the succeeded set is silently dropped."""
    versions = _registry.detect_versions({"definitely-not-a-real-engine"})
    assert versions == {}


def _fake_run(stdout: str):
    """A run_capture stub that returns the given stdout."""
    import subprocess

    def _stub(cmd, **kwargs):
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=stdout, stderr="")

    return _stub


def test_default_version_command_is_dash_dash_version(monkeypatch) -> None:
    """An engine without a `version_command` override uses `--version`."""
    import subprocess

    captured: list[list[str]] = []

    def _capture(cmd, **kwargs):
        captured.append(cmd)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="1.96.0\n", stderr="")

    monkeypatch.setattr(_registry, "require", lambda _: "/usr/local/bin/semgrep")
    monkeypatch.setattr(_registry, "run_capture", _capture)

    version = _registry.get("semgrep").detect_version()
    assert version == "1.96.0"
    assert captured == [["semgrep", "--version"]]


def test_scorecard_uses_subcommand_and_pattern(monkeypatch) -> None:
    """Scorecard rejects `--version`. It uses a `version` subcommand and
    prints the version inside ASCII art — we extract `GitVersion`.
    """
    scorecard_output = (
        "         __  ____     ____    ___\n"
        "./scorecard: OpenSSF Scorecard\n"
        "\n"
        "GitVersion:    v5.5.0\n"
        "GitCommit:     deadbeef\n"
    )
    monkeypatch.setattr(_registry, "require", lambda _: "/usr/local/bin/scorecard")
    monkeypatch.setattr(_registry, "run_capture", _fake_run(scorecard_output))
    assert _registry.get("scorecard").detect_version() == "v5.5.0"


def test_trivy_extracts_semver_from_version_line(monkeypatch) -> None:
    """Trivy prints `Version: 0.70.0` then DB info. Keep just the SemVer."""
    monkeypatch.setattr(_registry, "require", lambda _: "/usr/local/bin/trivy")
    monkeypatch.setattr(
        _registry, "run_capture", _fake_run("Version: 0.70.0\nVulnerabilityDB:\n  Version: 2\n")
    )
    assert _registry.get("trivy").detect_version() == "0.70.0"


def test_missing_binary_returns_unknown(monkeypatch) -> None:
    from stackhealth.engines._tools import EngineUnavailable

    def _raise(_binary):
        raise EngineUnavailable("not on PATH")

    monkeypatch.setattr(_registry, "require", _raise)
    assert _registry.get("semgrep").detect_version() == UNKNOWN_TOOL_VERSION


def test_pattern_no_match_returns_unknown(monkeypatch) -> None:
    """If the binary output doesn't contain a version, return UNKNOWN
    rather than guessing — better than silently shipping a wrong value.
    """
    monkeypatch.setattr(_registry, "require", lambda _: "/usr/local/bin/scorecard")
    monkeypatch.setattr(_registry, "run_capture", _fake_run("no version anywhere here"))
    assert _registry.get("scorecard").detect_version() == UNKNOWN_TOOL_VERSION
