# Changelog

All notable changes to StackHealth land here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
for the API surface (separate from the scoring formula's own versioning —
see `docs/03-SCORING-METHODOLOGY.md`).

## [Unreleased]

### Added
- Project front door — `LICENSE` (MIT, with explicit attribution clause),
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, issue and PR
  templates, Dependabot config, CODEOWNERS.

## [0.1.0] — 2026-05-29

The MVP, ready for a private beta.

### Added

- **Web frontend** (Next.js 15, App Router, TypeScript, Tailwind)
  - Landing page with URL input, sidebar showing Recent + Leaderboard,
    sample report cards
  - Scan progress page with real status transitions, bookmark-friendly
    report URL, and mid-scan email opt-in
  - Report page with grade hero, 4 sub-score cards with mini bars,
    dimension-grouped engine breakdown (Security / Quality / Hygiene /
    Community), real hygiene + test-signal checklists, default branch
    chip, clickable commit SHA, embed snippet
  - Methodology page rendering the open formula's weights and
    thresholds
  - **github.com → stackhealth.dev URL swap** — paste
    `stackhealth.dev/owner/repo` to jump straight to the latest report
  - Open Graph + Apple touch icon + favicon generated from JSX (no
    binary assets)
- **API** (FastAPI + SQLAlchemy 2)
  - `POST /api/scans` with optional `notify_email`
  - `GET /api/scans/{id}` and `/findings` (paginated)
  - `PATCH /api/scans/{id}/notify` for mid-scan email subscription
  - `GET /api/repos/{owner}/{name}` and `/latest`
  - `GET /api/discover/recent` and `/api/discover/top` for the public
    feed and leaderboard, edge-cached for 60s
  - `GET /r/{owner}/{name}/badge.svg` for embeddable badges
  - `GET /api/health` and `/api/stats`
  - CORS allows `GET, POST, PATCH, DELETE, OPTIONS`
  - Per-IP rate limit (5 scans/hour), per-repo dedupe (1/hour)
- **Worker** (RQ)
  - Shallow clone with 30s timeout and 500 MB cap; ephemeral tmpdir;
    no install steps, no test execution
  - Seven scoring engines: cloc, semgrep, trivy, OpenSSF Scorecard
    (with `api.scorecard.dev` cache fallback to local binary), lizard
    (cyclomatic complexity), jscpd (duplication), language-dispatched
    lint (ruff / eslint / golangci-lint)
  - Hygiene engine (13-item filesystem checklist) and test-signal
    engine (no test execution, just presence signals)
  - Community signals via GitHub REST API (activity, contributors,
    popularity, responsiveness)
  - Per-engine error isolation: a missing or failing engine marks
    `partial=true` and the scan still completes
  - Real status transitions (`cloning → analyzing → scoring →
    complete`) so the polling UI reflects reality
- **Formula v1.0**
  - Weights: Security 30%, Quality 25%, Hygiene 25%, Community 20%
  - Letter grades A+ through F with documented thresholds
  - Formula lives in `apps/api/stackhealth/formula/v1.py`, mirrored in
    `docs/03-SCORING-METHODOLOGY.md` and
    `packages/formula-spec/v1.0.md`
- **Email notifications** via Resend (free tier)
  - Polished HTML template — branded header, grade badge, sub-score
    grid, CTA button, methodology link, mobile-friendly
  - Plain-text alternative for accessibility / older clients
  - Falls back to log-only when `RESEND_API_KEY` is unset (dev-friendly)
- **Operations**
  - Local docker-compose with API + worker + web reaching the host's
    Postgres + Redis via `host.docker.internal`
  - Production docker-compose with Postgres + Redis + Caddy (auto-TLS)
  - GitHub Actions CI: ruff + pytest + Next.js build + lint
  - GitHub Actions Deploy workflow: opt-in SSH-based deploy gated on
    repo secrets

### Reproducibility

Every scan stores `formula_version`, the scanned commit SHA, and the
versions of every tool that ran. Anyone can fetch the raw artifacts and
recompute the score from the published formula. If the score doesn't
match, that is a bug.

[Unreleased]: https://github.com/santosh3743/stackhealth/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/santosh3743/stackhealth/releases/tag/v0.1.0
