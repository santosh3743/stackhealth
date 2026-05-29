"""Neutral defaults used when an optional engine fails or is unavailable.

These exist because every engine is allowed to fail — when one does, the
pipeline still produces a complete score. The values here are the
documented neutrals we substitute, picked so the resulting overall isn't
strongly biased either direction.

If you change any of these, also note it in docs/03-SCORING-METHODOLOGY.md
under "Partial scans" so the methodology stays in sync.
"""

# --- Security ---
# Picked at 5.0 / 10 so the contribution after scaling (x10) is the
# neutral midpoint of the 0-100 axis.
NEUTRAL_SCORECARD_AGGREGATE = 5.0

# Semgrep neutral leans slightly optimistic — most repos that fail
# semgrep do so because of timeouts on huge codebases, not because they
# have many findings.
NEUTRAL_SEMGREP_SCORE = 75

# Dependency penalty defaults — slight optimism (most projects are
# patched within a few weeks of disclosure).
NEUTRAL_DEPENDENCY_SCORE = 80

# --- Quality ---
NEUTRAL_COMPLEXITY_SCORE = 75
NEUTRAL_LINT_SCORE = 80
NEUTRAL_DUPLICATION_SCORE = 85
NEUTRAL_FILE_SIZE_SCORE = 50  # cloc failing means we can't measure files


# --- Tool version fallback ---
# Used when a tool ran successfully but we couldn't extract its version
# string (e.g. tool doesn't support --version).
UNKNOWN_TOOL_VERSION = "unknown"
