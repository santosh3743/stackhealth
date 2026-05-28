# StackHealth — formula spec

> The frozen, published versions of the StackHealth scoring formula.
>
> This directory is mirrored to the public repo `stackhealth-dev/formula` and tagged at each release. The README/Vision principle of an **open formula** means this is the canonical machine-readable record. Anyone can fork, recompute, or propose changes via PR.

## Files

| File | Contents |
|------|----------|
| `v1.0.md` | Human-readable frozen spec for formula v1.0 (mirror of `docs/03-SCORING-METHODOLOGY.md` as of the v1.0 tag) |
| `formula.json` | Machine-readable summary of weights and thresholds (consumed by the API for self-documentation) |

## Versioning

- **Patch (v1.0 → v1.0.1):** typo / wording fixes only. No score changes.
- **Minor (v1.0 → v1.1):** new optional engines, threshold tweaks. Old scans keep their original score; users can re-scan to get the new score.
- **Major (v1 → v2):** structural change. Preceded by a 30-day public RFC.

## Synchronisation

Three files MUST stay in lockstep:

1. `docs/03-SCORING-METHODOLOGY.md` — the working document
2. `packages/formula-spec/v1.0.md` (and future versions) — the frozen public copy
3. `apps/api/stackhealth/formula/v1.py` — the executable implementation

A change to one without the others is a bug. CI (TODO Phase 2) will assert they match.
