# StackHealth

> The open code health benchmark. Paste a GitHub URL. Get a score. Share it.

**Status:** Scaffolded. Not yet shipped. Target MVP launch: 4 weeks from kickoff.

For the full vision, methodology, and roadmap, see [`docs/README.md`](docs/README.md).

---

## Tech stack

- **Frontend:** Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui → Vercel
- **API + Worker:** FastAPI + RQ (Redis Queue) + SQLAlchemy 2 → Fly.io
- **Database:** Postgres 16 → Neon
- **Queue / cache:** Redis → Upstash
- **Object storage:** Cloudflare R2 (raw scan artifacts)
- **Package managers:** `pnpm` for JS, `uv` for Python

Full reasoning behind each choice: [`docs/05-TECH-STACK.md`](docs/05-TECH-STACK.md).

---

## Local development

### Prerequisites

- Node.js 20+ and `pnpm` 9+
- Python 3.12+ and `uv`
- Docker (for Postgres + Redis locally) **or** access to Neon + Upstash free tiers
- `git`, `cloc`, `semgrep`, `trivy` on PATH (worker only — see `infra/Dockerfile` for versions)

### One-time setup

```bash
git clone https://github.com/santosh3743/stackhealth
cd stackhealth
./scripts/setup.sh
```

The setup script:
1. Copies `.env.example` files into `.env.local`
2. Runs `pnpm install` in `apps/web`
3. Runs `uv sync` in `apps/api`
4. Reminds you what to fill in `.env.local`

### Run everything (three terminals)

```bash
# Terminal 1: web
cd apps/web
pnpm dev                    # http://localhost:3000

# Terminal 2: API
cd apps/api
uv run uvicorn stackhealth.api.main:app --reload --port 8000

# Terminal 3: worker
cd apps/api
uv run rq worker --url $REDIS_URL stackhealth
```

### Migrations

```bash
cd apps/api
uv run alembic upgrade head           # apply all migrations
uv run alembic revision --autogenerate -m "describe change"
```

### Tests

```bash
cd apps/web && pnpm test
cd apps/api && uv run pytest
```

---

## Deployment

Two Fly.io apps (API + worker), one Vercel project (web). Configs are in `infra/`.

```bash
# First-time
fly launch --config infra/fly.api.toml --name stackhealth-api
fly launch --config infra/fly.worker.toml --name stackhealth-worker

# Subsequent deploys (via GitHub Actions on push to main)
fly deploy --config infra/fly.api.toml
fly deploy --config infra/fly.worker.toml
```

Web auto-deploys via Vercel's GitHub integration.

Full cost breakdown in [`docs/11-INFRASTRUCTURE-AND-COSTS.md`](docs/11-INFRASTRUCTURE-AND-COSTS.md).

---

## Project documentation

| Topic | Doc |
|-------|-----|
| Why this exists | [`docs/01-VISION.md`](docs/01-VISION.md) |
| What it does | [`docs/02-PRODUCT-SPEC.md`](docs/02-PRODUCT-SPEC.md) |
| **The open formula** | [`docs/03-SCORING-METHODOLOGY.md`](docs/03-SCORING-METHODOLOGY.md) |
| System design | [`docs/04-ARCHITECTURE.md`](docs/04-ARCHITECTURE.md) |
| Tech choices | [`docs/05-TECH-STACK.md`](docs/05-TECH-STACK.md) |
| Roadmap | [`docs/06-ROADMAP.md`](docs/06-ROADMAP.md) |
| **Day-by-day build plan** | [`docs/07-MVP-BUILD-PLAN.md`](docs/07-MVP-BUILD-PLAN.md) |
| Data model | [`docs/08-DATA-MODEL.md`](docs/08-DATA-MODEL.md) |
| API design | [`docs/09-API-DESIGN.md`](docs/09-API-DESIGN.md) |
| Frontend pages | [`docs/10-FRONTEND-PAGES.md`](docs/10-FRONTEND-PAGES.md) |
| Costs | [`docs/11-INFRASTRUCTURE-AND-COSTS.md`](docs/11-INFRASTRUCTURE-AND-COSTS.md) |
| Security | [`docs/12-SECURITY-AND-PRIVACY.md`](docs/12-SECURITY-AND-PRIVACY.md) |
| Launch & growth | [`docs/13-LAUNCH-AND-GROWTH.md`](docs/13-LAUNCH-AND-GROWTH.md) |
| Competitors | [`docs/14-COMPETITORS.md`](docs/14-COMPETITORS.md) |

For Claude Code orientation, see [`CLAUDE.md`](CLAUDE.md).

---

## License

MIT for the application. The scoring formula (in `packages/formula-spec/`) is CC0 — anyone can fork, reuse, or argue with it.
