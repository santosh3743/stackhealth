# 05 — Tech Stack

## At a glance

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend framework | Next.js 15 (App Router) | SEO matters for report pages; ISR is perfect for them; you already know it. |
| Language (FE) | TypeScript | Default. No drama. |
| Styling | Tailwind CSS 4 + shadcn/ui | Speed of execution. Consistent design. |
| Forms / state | React 19 + Tanstack Query | Polling status pages cleanly. |
| Frontend hosting | Vercel | Free tier covers MVP. Best Next.js DX. |
| API framework | FastAPI | You know it from Zeron. Auto-OpenAPI. |
| Language (BE) | Python 3.12 | Same. Worker shares libraries with API. |
| ORM | SQLAlchemy 2 + Pydantic v2 | Standard combo with FastAPI. |
| Migrations | Alembic | Same as Zeron. |
| Job queue | RQ (Redis Queue) | Simpler than Celery. One Python process, dead-simple. |
| Database | Postgres 16 on Neon | Free tier, branching for staging. |
| Cache / queue store | Redis on Upstash | Serverless Redis, free tier. |
| Object storage | Cloudflare R2 | Zero egress fee, cheap. |
| API + worker hosting | Fly.io | Always-on containers, cheap, multi-region. |
| Domain | `stackhealth.dev` | $12/year. `.dev` is HTTPS-enforced. |
| Email | Resend (later) | Cheap, good API. Only after Phase 2. |
| Auth (later) | Auth.js + GitHub OAuth | Standard. |
| Analytics | Plausible (cloud) | Privacy-respecting, $9/month. Self-host later. |
| Error tracking | Sentry free tier | Standard. |
| CI / CD | GitHub Actions | Native. |
| Package manager (FE) | pnpm | Faster than npm. |
| Package manager (BE) | uv | 10x pip. Fast in CI. |

---

## Frontend deep dive

### Why Next.js App Router

- **SEO is critical.** Report pages need to rank for "stackhealth `repo-name`" queries. App Router's server components and metadata API are best-in-class.
- **ISR for report pages.** A report is computed once, then mostly static. ISR with on-demand revalidation (when a new scan completes) gives Vercel-edge-cached pages with sub-100ms TTFB.
- **Streaming UI.** The scan-progress page benefits from React Suspense streaming.
- **You already know it.** From the Zeron `grc-ui`, `posture-ui`, etc.

### Component library

shadcn/ui (Radix + Tailwind). Copy-in components, no runtime dependency, fully customizable. Specifically:

- `Card` — sub-score cards
- `Tabs` — Findings / Methodology / Raw artifacts
- `Accordion` — finding groups
- `Progress` — scan progress bar
- `Tooltip` — score explainers
- `Dialog` — share modal
- `Code` (custom) — for the YAML/JSON snippets in raw artifacts

### Why NOT Vite + React Router

- Loses SEO out of the box (CSR-only by default)
- Loses ISR
- The only thing it would buy us is faster local dev, which doesn't matter at this scale

---

## Backend deep dive

### Why FastAPI

- You know it from Zeron — `zeron-compliance`, `vrm-api`, `insure-api`, etc. all use it.
- Pydantic v2 validates request bodies for free.
- Auto OpenAPI gives us `/api/docs` without effort.
- Async support lets us call GitHub API non-blocking from the API process.

### Why RQ over Celery

| | Celery | RQ |
|--|--------|-----|
| Setup complexity | High (brokers, results backends, queues) | Low (just Redis) |
| Operational complexity | Workers crash mysteriously | Workers crash predictably |
| Feature set | Massive (we need ~10%) | Minimal (we need ~95%) |
| Documentation | Vast but scattered | One readme |
| Solo-friendliness | Bad | Good |

We can swap to Celery in Phase 4 if we ever need things like scheduled tasks (we'll use cron jobs in Fly.io instead for MVP), priority queues, or task chains.

### Why Postgres on Neon

- Free tier: 0.5 GB, branching for staging, autopause.
- We can do all our metadata in JSON columns if needed (JSONB).
- Same dialect as everything you've used at Zeron.

Alternatives considered:
- **SQLite + Litestream** — Tempting for simplicity, but multi-process (API + worker) sharing SQLite is awkward.
- **Supabase** — Bundles auth/DB/storage, but locks us in and we'd pay for features we use differently.

### Why Cloudflare R2

- **Zero egress.** Raw scan outputs are public; if a popular report's artifacts get fetched, we don't get a surprise AWS bill.
- $0.015/GB/month storage.
- S3-compatible API; works with `boto3`.

---

## Infrastructure deep dive

### Why Fly.io for API + worker

- Always-on (no cold starts) — important because the worker needs to be ready when jobs arrive.
- Cheap shared-cpu-1x machines: $1.94/month each at 256MB RAM. We'll run 2 (one API, one worker) = ~$4/month.
- Multi-region trivially via `fly regions add`.
- `fly.toml` config is straightforward.
- Postgres extensions (`fly mpg`) if Neon ever becomes a problem.

Alternatives:
- **Railway** — Similar, but ~2x more expensive at our scale.
- **Render** — Free tier sleeps; paid tier comparable to Fly.
- **VPS (Hetzner, DO)** — Cheapest option but more ops work.

### Why Vercel for frontend

- Free hobby tier covers 100GB bandwidth, plenty for MVP.
- Best Next.js performance and DX.
- Edge functions + ISR built-in.
- Easy preview deploys per PR.

If we hit Vercel's $20/month commercial-use limit (we will, when StackHealth becomes a business), we move to Cloudflare Pages or self-host on Fly.

---

## Why we're NOT using…

- **Docker Compose for local dev:** We will use `uv` + `pnpm` natively. A `Dockerfile` exists only for Fly.io deploys.
- **Kubernetes:** Wildly overkill.
- **Microservices:** We have one API and one worker. That's two services. Not micro.
- **GraphQL:** REST + OpenAPI is simpler and the API is small.
- **Tailwind UI ($$):** shadcn/ui is free and equally good for our needs.
- **A monorepo tool (Turbo, Nx):** Folder-based separation is fine at this scale.

---

## Repository structure

```
stackhealth/
├── apps/
│   ├── web/                # Next.js
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   └── api/                # FastAPI + worker (shared codebase)
│       ├── stackhealth/
│       │   ├── api/        # FastAPI routes
│       │   ├── worker/     # RQ jobs
│       │   ├── engines/    # scorecard.py, semgrep.py, trivy.py, ...
│       │   ├── formula/    # formula.py (the open spec, in code)
│       │   ├── models/     # SQLAlchemy
│       │   └── schemas/    # Pydantic
│       ├── alembic/
│       ├── tests/
│       └── pyproject.toml
├── packages/
│   └── formula-spec/       # Markdown spec (mirrors 03-SCORING-METHODOLOGY.md)
├── infra/
│   ├── fly.api.toml
│   ├── fly.worker.toml
│   └── Dockerfile
├── .github/workflows/
└── README.md
```

`packages/formula-spec/` is published as its own GitHub repository (`stackhealth/formula`) so people can star, watch, and PR against it independently of the app.
