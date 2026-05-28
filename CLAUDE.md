# Claude Code — StackHealth project orientation

> Read this file first. Then read `docs/README.md`. Then check `docs/TODO.md` for the current task.

## What this project is

**StackHealth** is an open-formula code health benchmark. A user pastes a public GitHub URL on `stackhealth.dev`, and within ~90 seconds gets a letter grade (A+ to F) backed by four sub-scores (Security, Quality, Hygiene, Community) with every finding, weight, and threshold publicly documented.

One-line pitch: *Lighthouse for any GitHub repo, with a fully open scoring formula.*

## Where everything is documented

All planning lives in `docs/`. The complete index is in `docs/README.md`. The files that matter most for any code work:

| File | Why you'll need it |
|------|--------------------|
| `docs/03-SCORING-METHODOLOGY.md` | The open formula. Source of truth for any scoring logic. |
| `docs/04-ARCHITECTURE.md` | Components, data flow, failure modes |
| `docs/07-MVP-BUILD-PLAN.md` | **Day-by-day plan for the next 4 weeks. Start here.** |
| `docs/08-DATA-MODEL.md` | Postgres schema (matches `apps/api/alembic/versions/001_initial.py`) |
| `docs/09-API-DESIGN.md` | FastAPI endpoint specs |
| `docs/10-FRONTEND-PAGES.md` | Next.js pages, components, visual identity |
| `docs/12-SECURITY-AND-PRIVACY.md` | Scanning sandbox rules — read before touching the worker |
| `docs/TODO.md` | Live action list. Update at end of every session. |

## Repository layout

```
StackHealth/
├── CLAUDE.md                ← you are here
├── README.md                ← dev README (setup, run, deploy)
├── docs/                    ← all planning + methodology
├── apps/
│   ├── web/                 ← Next.js 15 frontend
│   └── api/                 ← FastAPI + RQ worker (shared codebase)
├── packages/
│   └── formula-spec/        ← published spec for `stackhealth-dev/formula`
├── infra/                   ← Dockerfile + fly.toml configs
├── scripts/                 ← setup.sh and dev helpers
└── .github/workflows/       ← CI
```

`apps/api` is one Python package that runs as **two processes**: the FastAPI HTTP server (`stackhealth.api.main:app`) and the RQ worker (`stackhealth.worker.main`). They share models, DB connection, and engines.

## Current state

The project is **scaffolded but not yet implemented**. The folder structure, all configs, all docs, and stub files are in place. Approximate state per the build plan in `docs/07-MVP-BUILD-PLAN.md`:

- ✅ Week 0 foundations — scaffolding complete
- 🔲 Week 1 — Skeleton (not started)
- 🔲 Week 2 — Scoring pipeline 1/2
- 🔲 Week 3 — Scoring pipeline 2/2
- 🔲 Week 4 — Polish + launch

**Your next action when starting a session:** read `docs/TODO.md`, find the next unchecked item, do it, mark it done, update notes.

## Hard rules

These come from the docs but are worth restating so they're not missed:

1. **The formula is in `apps/api/stackhealth/formula/v1.py` and mirrored in `packages/formula-spec/v1.0.md` and `docs/03-SCORING-METHODOLOGY.md`. These three must stay in sync.** If you change one, change all three.
2. **The worker never executes repo code.** Only static analysis. No `pip install`, no `npm install`, no `make`, no tests. See `docs/12-SECURITY-AND-PRIVACY.md`.
3. **Shallow clone only** (`git clone --depth 1`). Hard 30s clone timeout, 500 MB clone size cap, 5-min wall-clock scan timeout.
4. **We only scan public repos in MVP.** API rejects private/missing repos before enqueueing.
5. **Every scan stores `formula_version` and tool versions.** Reproducibility guarantee.
6. **Rate limit:** 5 scans/IP/hour anonymous, 1 scan/repo/hour globally.

## How to run locally

See `README.md` (at the root) for the full setup. TL;DR:

```bash
# One-time setup
./scripts/setup.sh

# Run the web app
cd apps/web && pnpm dev          # http://localhost:3000

# Run the API
cd apps/api && uv run uvicorn stackhealth.api.main:app --reload --port 8000

# Run the worker
cd apps/api && uv run rq worker --url $REDIS_URL stackhealth
```

## Conventions

- **Branch naming:** `feat/<area>-<short>`, `fix/<area>-<short>`. Area is one of `web`, `api`, `worker`, `engines`, `formula`, `infra`, `docs`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`).
- **TypeScript:** Strict mode. No `any` without a comment explaining why.
- **Python:** `ruff format` + `ruff check`. Type hints everywhere. Pydantic v2 for schemas.
- **Tests:** pytest for API/worker, Vitest for web. Smoke tests at minimum for new endpoints.
- **Migrations:** Alembic. Never destructive without explicit confirmation. Review the generated SQL before running.

## How to think about scope

If a task feels bigger than what's listed for the current day in `docs/07-MVP-BUILD-PLAN.md`, **stop and ask the user**. The plan is opinionated; don't expand it without an explicit decision. Better to ship Week 1's deliverable on Sunday evening than to half-finish Week 1 + Week 2 by Sunday.

## When in doubt

Default to the principles in `docs/01-VISION.md`:
1. Open formula (transparency over cleverness)
2. Free for public repos forever
3. Shareable by default (permalinks, badges)
4. Peer-reviewable (every claim has raw output behind it)
5. Reproducible (same inputs → same score)

These five rules resolve most ambiguity.
