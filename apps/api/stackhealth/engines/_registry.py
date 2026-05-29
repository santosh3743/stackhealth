"""Engine registry.

Captures the cross-cutting metadata about every engine the pipeline knows
about — name (used in DB enums + UI labels), and how to ask the underlying
binary for its version string.

The `run()` signatures intentionally aren't part of this protocol because
they legitimately vary: some engines take a workdir, some take (owner,
name), some take additional context like detected languages.

The registry's main payoff: a single source of truth for "what engines
exist" and how to get their versions for the scan's reproducibility
manifest. Before this, pipeline.py had a scattered set of
`tool_vers["x"] = tool_version("x") or UNKNOWN` lines that drifted
(scorecard was hardcoded "5.x" instead of detected).
"""

import re
from dataclasses import dataclass, field

from stackhealth.engines._tools import EngineFailed, EngineUnavailable, require, run_capture
from stackhealth.formula.defaults import UNKNOWN_TOOL_VERSION


@dataclass(frozen=True)
class EngineDescriptor:
    """A registered scanning engine.

    Attributes:
        name: Stable identifier used in DB enums, UI labels, and
            failure messages. Must match `FindingEngine` values for any
            engine that produces persisted findings.
        binary: External binary to query. `None` for pure-Python
            engines (hygiene, test_signal, community).
        version_command: Args to pass to the binary to get the version.
            Defaults to `("--version",)`. Scorecard overrides this to
            `("version",)` because it uses a subcommand.
        version_pattern: Optional regex to extract the version string
            from the binary's output. Group 1 is taken. If unset, the
            first non-empty line of stdout is used.
    """

    name: str
    binary: str | None = None
    version_command: tuple[str, ...] = field(default=("--version",))
    version_pattern: str | None = None

    def detect_version(self) -> str:
        """Returns the binary's version string, or UNKNOWN_TOOL_VERSION."""
        if self.binary is None:
            return UNKNOWN_TOOL_VERSION
        try:
            require(self.binary)
        except EngineUnavailable:
            return UNKNOWN_TOOL_VERSION
        try:
            proc = run_capture([self.binary, *self.version_command], timeout=10)
        except EngineFailed:
            return UNKNOWN_TOOL_VERSION

        output = (proc.stdout or proc.stderr).strip()
        if not output:
            return UNKNOWN_TOOL_VERSION

        if self.version_pattern:
            match = re.search(self.version_pattern, output)
            if match:
                return match.group(1)
            return UNKNOWN_TOOL_VERSION

        return output.splitlines()[0]


# Order is for documentation / UI; pipeline doesn't iterate by index.
REGISTRY: tuple[EngineDescriptor, ...] = (
    EngineDescriptor("cloc", "cloc"),
    EngineDescriptor("hygiene"),  # pure-Python, no binary
    EngineDescriptor("test_signal"),
    EngineDescriptor("semgrep", "semgrep"),
    # Trivy's `--version` output is "Version: 0.70.0\n…" — take just the SemVer.
    EngineDescriptor(
        "trivy",
        "trivy",
        version_pattern=r"Version:\s+(\d+\.\d+\.\d+)",
    ),
    EngineDescriptor("lizard", "lizard"),
    EngineDescriptor("jscpd", "jscpd"),
    # Scorecard refuses `--version` and instead prints version via a
    # `version` subcommand, surrounded by ASCII art. We pull `GitVersion`.
    EngineDescriptor(
        "scorecard",
        "scorecard",
        version_command=("version",),
        version_pattern=r"GitVersion:\s+(v?\d+\.\d+\.\d+)",
    ),
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
