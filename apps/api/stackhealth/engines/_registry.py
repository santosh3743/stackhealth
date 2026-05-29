"""Engine registry.

Captures the cross-cutting metadata about every engine the pipeline knows
about — name (used in DB enums + UI labels), and the binary name to query
for `--version`. The `run()` signatures intentionally aren't part of this
protocol because they legitimately vary: some engines take a workdir, some
take (owner, name), some take additional context like detected languages.

The registry's main payoff: a single source of truth for "what engines
exist" and how to get their versions for the scan's reproducibility
manifest. Before this, pipeline.py had a scattered set of
`tool_vers["x"] = tool_version("x") or UNKNOWN` lines that drifted
(scorecard was hardcoded "5.x" instead of detected).
"""

from dataclasses import dataclass

from stackhealth.engines._tools import tool_version
from stackhealth.formula.defaults import UNKNOWN_TOOL_VERSION


@dataclass(frozen=True)
class EngineDescriptor:
    """A registered scanning engine.

    Attributes:
        name: Stable identifier used in DB enums, UI labels, and
            failure messages. Must match `FindingEngine` values for any
            engine that produces persisted findings.
        binary: External binary to query with `--version`. `None` for
            pure-Python engines (hygiene, test_signal, community, lint —
            though lint dispatches to ruff/eslint/golangci, those are
            tracked separately by lint.py itself).
    """

    name: str
    binary: str | None = None

    def detect_version(self) -> str:
        """Returns the binary's version string, or UNKNOWN_TOOL_VERSION."""
        if self.binary is None:
            return UNKNOWN_TOOL_VERSION
        return tool_version(self.binary) or UNKNOWN_TOOL_VERSION


# Order is for documentation / UI; pipeline doesn't iterate by index.
REGISTRY: tuple[EngineDescriptor, ...] = (
    EngineDescriptor("cloc", "cloc"),
    EngineDescriptor("hygiene"),  # pure-Python, no binary
    EngineDescriptor("test_signal"),
    EngineDescriptor("semgrep", "semgrep"),
    EngineDescriptor("trivy", "trivy"),
    EngineDescriptor("lizard", "lizard"),
    EngineDescriptor("jscpd", "jscpd"),
    EngineDescriptor("scorecard", "scorecard"),
    EngineDescriptor("lint"),
    EngineDescriptor("community"),
    EngineDescriptor("github_meta"),
)


_BY_NAME = {e.name: e for e in REGISTRY}


def get(name: str) -> EngineDescriptor:
    """Look up an engine by name. Raises KeyError if unknown."""
    return _BY_NAME[name]


def detect_versions(succeeded_engines: set[str]) -> dict[str, str]:
    """Build the `tool_versions` map for a scan.

    Only includes engines that actually succeeded — failed engines
    don't get a version recorded, which makes failures discoverable
    by comparing scan.tool_versions against the registry.
    """
    out: dict[str, str] = {}
    for engine_name in succeeded_engines:
        try:
            descriptor = get(engine_name)
        except KeyError:
            continue
        if descriptor.binary is not None:
            out[engine_name] = descriptor.detect_version()
    return out
