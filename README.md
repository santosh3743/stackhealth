<div align="center">

# StackHealth

**The open code health benchmark for any public GitHub repo.**

Paste a URL. Get a grade. Share the report.

[stackhealth.dev](https://stackhealth.dev) · [Methodology](https://stackhealth.dev/methodology) · [Contributing](./CONTRIBUTING.md)

[![CI](https://github.com/santosh3743/stackhealth/actions/workflows/ci.yml/badge.svg)](https://github.com/santosh3743/stackhealth/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/stackhealth?label=npm%3A%20stackhealth)](https://www.npmjs.com/package/stackhealth)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Formula v1.0](https://img.shields.io/badge/Formula-v1.0-4f46e5.svg)](https://stackhealth.dev/methodology)

<br/>

[![StackHealth scorecard](https://api.stackhealth.dev/r/santosh3743/stackhealth/card.svg)](https://stackhealth.dev/r/santosh3743/stackhealth)

</div>

---

StackHealth scores public GitHub repositories on **Security, Quality,
Hygiene, and Community** using a fully open scoring formula. Every
weight, every threshold, every engine output is documented and
inspectable. The goal is to give code what Lighthouse did for websites:
a defensible, public, reproducible health rating that maintainers and
adopters can both point at.

```
github.com/pallets/click   →   stackhealth.dev/pallets/click
```

That's the whole interaction. Submit a URL on the site, or just
**replace `github.com` with `stackhealth.dev`** in any repo URL. Within
~30–90 seconds you get a letter grade backed by seven engines.

---

## Three ways to use it

### 1. From your browser

Go to **[stackhealth.dev](https://stackhealth.dev)** and paste any
github.com URL — or just edit the URL bar. The leaderboard at
[stackhealth.dev/leaderboard](https://stackhealth.dev/leaderboard) shows
the highest-graded repos across languages.

### 2. From your terminal

```bash
$ npx stackhealth fastapi/fastapi
  fastapi/fastapi
  A   91/100

    Security   ████████████████████  100/100
    Quality    █████████████████···   85/100
    Hygiene    ████████████████████  100/100
    Community  ████████████████····   80/100
```

Pipe-friendly (`--json`), CI-friendly (`--min-grade B` returns
non-zero), and ref-aware (`--ref v8.0.0`). Full reference in
[`apps/cli/README.md`](./apps/cli/README.md).

### 3. From your pull requests

Drop this workflow into `.github/workflows/stackhealth.yml` and every PR
gets a sticky comment showing the base vs. PR grade, sub-dimension
breakdowns, and the delta.

```yaml
on:
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: santosh3743/stackhealth@v0
        with:
          email: ${{ secrets.STACKHEALTH_EMAIL }}
          min-grade: B    # optional gate
```

Full reference in [`apps/action/README.md`](./apps/action/README.md).

---

## What's under the score

| Dimension | Weight | What feeds it |
|---|---|---|
| **Security** | 30% | OpenSSF Scorecard · Semgrep (`p/security-audit`) · Trivy CVE scan |
| **Quality** | 25% | Cyclomatic complexity (lizard) · Lint density (ruff / eslint / golangci-lint) · Duplication (jscpd) · Test signal · File size |
| **Hygiene** | 25% | 13-point binary checklist: README, LICENSE, CONTRIBUTING, CI, tests, etc. |
| **Community** | 20% | Recent activity · Contributor count (log₂) · Stars (log₁₀) · Issue responsiveness |

The full formula lives in three sync'd places:
[`docs/03-SCORING-METHODOLOGY.md`](./docs/03-SCORING-METHODOLOGY.md)
(human-readable), [`packages/formula-spec/v1.0.md`](./packages/formula-spec)
(machine-readable, frozen), and
[`apps/api/stackhealth/formula/v1.py`](./apps/api/stackhealth/formula/v1.py)
(executable).

Every scan stores the formula version, scanned commit SHA, and tool
versions. Raw engine outputs are kept so anyone can recompute the score
from scratch. If the score doesn't match what the formula says it
should, that's a bug.

---

## What's in this repository

```
StackHealth/
├── apps/
│   ├── web/                    Next.js 15 frontend (TypeScript + Tailwind)
│   ├── api/                    FastAPI + RQ worker (Python 3.12)
│   │   ├── stackhealth/
│   │   │   ├── api/            HTTP routes (incl. discover, scans, badge)
│   │   │   ├── engines/        Scanning engines (semgrep, trivy, …)
│   │   │   ├── formula/        The open scoring formula
│   │   │   └── worker/         RQ jobs and the scan pipeline
│   │   └── alembic/            Database migrations
│   ├── cli/                    `npx stackhealth` — TypeScript, zero deps
│   └── action/                 GitHub Action — PR grade comments
├── packages/
│   └── formula-spec/           Frozen, machine-readable formula
├── docs/                       Vision, methodology, architecture, API design
├── infra/                      Dockerfile + docker-compose + Caddyfile
└── .github/                    CI, issue templates, dependabot, CODEOWNERS
```

A few documents that go deeper than this README:

- [`docs/01-VISION.md`](./docs/01-VISION.md) — why this exists
- [`docs/03-SCORING-METHODOLOGY.md`](./docs/03-SCORING-METHODOLOGY.md) — **the open formula**
- [`docs/04-ARCHITECTURE.md`](./docs/04-ARCHITECTURE.md) — system design
- [`docs/09-API-DESIGN.md`](./docs/09-API-DESIGN.md) — every endpoint
- [`docs/12-SECURITY-AND-PRIVACY.md`](./docs/12-SECURITY-AND-PRIVACY.md) — sandbox + threat model
- [`CONTRIBUTING.md`](./CONTRIBUTING.md) — how to set up and submit changes
- [`SECURITY.md`](./SECURITY.md) — responsible disclosure
- [`CHANGELOG.md`](./CHANGELOG.md) — what's shipped

---

## Run it locally

### Prerequisites

- Node.js 20+ and `pnpm` 9+
- Python 3.12+ and [`uv`](https://docs.astral.sh/uv/)
- Docker 24+ (for Postgres + Redis + the production-style local run)

### Containerized local run (recommended)

This is the closest path to how it runs in production. Spins up
Postgres, Redis, the API, the worker, the web app, and Caddy.

```bash
git clone https://github.com/santosh3743/stackhealth.git
cd stackhealth
cp infra/.env.prod.example .env
# Fill in DOMAIN, ACME_EMAIL, POSTGRES_PASSWORD, GITHUB_TOKEN
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d --build
```

See [`infra/README.md`](./infra/README.md) for the full deploy
walkthrough.

### Running the parts directly

If you'd rather hack on the API or web without Docker:

```bash
./scripts/setup.sh    # copies env templates, runs pnpm install + uv sync

# Terminal 1 — web
cd apps/web && pnpm dev                # http://localhost:3000

# Terminal 2 — API
cd apps/api && uv run uvicorn stackhealth.api.main:app --reload --port 8000

# Terminal 3 — worker
cd apps/api && uv run python -m stackhealth.worker.main
```

You'll need Postgres + Redis running somewhere (Docker, Homebrew,
managed services — your call). Set `DATABASE_URL` and `REDIS_URL` in
`apps/api/.env.local`. A `GITHUB_TOKEN` is optional but recommended
(lifts the GitHub API limit from 60/hr anonymous to 5,000/hr).

### Migrations

```bash
cd apps/api
uv run alembic upgrade head                           # apply
uv run alembic revision --autogenerate -m "describe"  # new revision
```

### Tests

```bash
cd apps/api && uv run pytest -q
cd apps/web && pnpm typecheck && pnpm lint && pnpm build
```

---

## API at a glance

The hosted API is at **`https://api.stackhealth.dev`**. Auto-generated
OpenAPI docs at [`/api/docs`](https://api.stackhealth.dev/api/docs).

```bash
# Submit a scan
curl -X POST https://api.stackhealth.dev/api/scans \
  -H 'Content-Type: application/json' \
  -d '{"repo_url": "https://github.com/pallets/click"}'

# Poll its status
curl https://api.stackhealth.dev/api/scans/<scan_id>

# Get the latest scan for a repo
curl https://api.stackhealth.dev/api/repos/pallets/click/latest

# Public feed
curl https://api.stackhealth.dev/api/discover/recent
curl https://api.stackhealth.dev/api/discover/top?language=Python

# Embeddable badge
https://api.stackhealth.dev/r/pallets/click/badge.svg
```

Full reference: [`docs/09-API-DESIGN.md`](./docs/09-API-DESIGN.md).

---

## Embed a badge or scorecard in your README

Two flavors, both always-latest, embed-and-forget:

```markdown
<!-- compact badge — fits anywhere alongside other shields -->
[![StackHealth](https://api.stackhealth.dev/r/OWNER/REPO/badge.svg)](https://stackhealth.dev/r/OWNER/REPO)

<!-- rich scorecard — 440 × 220 with sub-dimension bars -->
[![StackHealth scorecard](https://api.stackhealth.dev/r/OWNER/REPO/card.svg)](https://stackhealth.dev/r/OWNER/REPO)
```

The scorecard shows the overall grade, score, and all four
sub-dimensions in one image — what you see at the top of *this* README
is the live `card.svg` for the StackHealth repo itself.

The CLI can spit out the badge markdown for you:

```bash
$ npx stackhealth OWNER/REPO --badge
[![StackHealth](https://api.stackhealth.dev/r/OWNER/REPO/badge.svg)](https://stackhealth.dev/r/OWNER/REPO)
```

---

## Contributing

The most useful contributions right now are:

1. **Bug reports** with a reproducer URL.
2. **Calibration data** — repos whose scores feel wrong, with a
   rationale.
3. **Pull requests** improving engines, tightening sandbox boundaries,
   or polishing the report UI.
4. **Proposals against the formula** — these go through a documented
   review process. See
   [Changing the scoring formula](./CONTRIBUTING.md#changing-the-scoring-formula).

Before opening anything substantial, please read
[`CONTRIBUTING.md`](./CONTRIBUTING.md) and the
[Code of Conduct](./CODE_OF_CONDUCT.md).

Security issues go through the private disclosure flow in
[`SECURITY.md`](./SECURITY.md) — please don't open public issues for
them.

---

## License

[MIT](./LICENSE), with the explicit requirement that the original
copyright notice and attribution to **Santosh Jha** be preserved in any
copy or substantial portion. You may use, fork, modify, and
redistribute, including commercially — credit the author and don't
remove the copyright notice.

The scoring methodology, documentation, and source code are all
covered by this license; copyright is retained by the author.
