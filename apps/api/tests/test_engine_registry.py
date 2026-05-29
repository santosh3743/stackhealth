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


def test_detect_versions_includes_present_binary(monkeypatch) -> None:
    """When tool_version() returns a string, it lands in the result."""
    monkeypatch.setattr(
        _registry,
        "tool_version",
        lambda binary: "1.2.3",
    )
    versions = _registry.detect_versions({"semgrep"})
    assert versions == {"semgrep": "1.2.3"}


def test_detect_versions_falls_back_to_unknown(monkeypatch) -> None:
    """When the binary is missing tool_version() returns None — we substitute
    the UNKNOWN constant rather than dropping the engine.
    """
    monkeypatch.setattr(
        _registry,
        "tool_version",
        lambda binary: None,
    )
    versions = _registry.detect_versions({"semgrep"})
    assert versions == {"semgrep": UNKNOWN_TOOL_VERSION}
