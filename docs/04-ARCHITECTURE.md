# 04 — Architecture

## High-level diagram

```
                                ┌──────────────────────────┐
                                │   stackhealth.dev         │
                                │   (Next.js on Vercel)     │
                                └────────────┬──────────────┘
                                             │ HTTPS / JSON
                                             ▼
                          ┌──────────────────────────────────┐
                          │      API (FastAPI on Fly.io)      │
                          │   /api/scans, /api/repos, ...     │
                          └───┬──────────────┬───────────────┘
                              │              │
                              │              │  (enqueue job)
                              ▼              ▼
              ┌───────────────────────┐  ┌──────────────────────┐
              │   Postgres (Neon)      │  │   Redis (Upstash)     │
              │   repos, scans,        │  │   RQ job queue +      │
              │   findings, formula    │  │   rate-limit counters │
              └───────────────────────┘  └──────────┬───────────┘
                                                     │
                                                     ▼
                                  ┌──────────────────────────────┐
                                  │   Worker (FastAPI sibling on  │
                                  │   Fly.io, runs RQ)            │
                                  │                                │
                                  │   1. shallow git clone         │
                                  │   2. parallel: cloc, scorecard,│
                                  │      semgrep, trivy, lint      │
                                  │   3. compute formula           │
                                  │   4. write findings to Postgres│
                                  │   5. upload raw outputs to R2  │
                                  └──────────────────┬─────────────┘
                                                     │
                                                     ▼
                                 ┌────────────────────────────────┐
                                 │  Cloudflare R2 (object store)  │
                                 │  raw JSON outputs per scan      │
                                 │  (publicly readable)            │
                                 └────────────────────────────────┘
```

External services touched:
- **GitHub REST API** — repo metadata, stars, issue stats
- **OpenSSF Scorecard API** (`api.scorecard.dev`) — Scorecard results when available

---

## Component responsibilities

### Frontend — Next.js 15 (App Router)

- Server components for landing, methodology, about (SEO-critical)
- Client components for scan submission, live progress polling, badge embed UI
- ISR (Incremental Static Regeneration) for report pages: regenerate once per scan, then cache
- Tailwind + shadcn/ui for design system
- Deployed to Vercel free tier (sufficient for MVP)

### API — FastAPI

- Stateless HTTP service
- Endpoints listed in `09-API-DESIGN.md`
- Validates repo URLs, calls GitHub for public-repo verification, creates `Scan` records, enqueues to RQ
- Reads/writes Postgres
- Serves badge SVGs (cached via Cache-Control headers)
- Auth-less in MVP; designed to bolt on GitHub OAuth in Phase 2

### Worker — RQ (Redis Queue)

- Same Python codebase as API, deployed as a separate process
- Pulls jobs from Redis, runs the scan pipeline
- One worker process can handle ~2 concurrent scans (each takes ~60–120s, parallel engines)
- Horizontally scalable — add more Fly.io machines if queue depth grows

### Database — Postgres (Neon)

- Schema in `08-DATA-MODEL.md`
- Free tier (0.5 GB) easily fits MVP
- Branching for staging — Neon's killer feature

### Cache + Queue — Redis (Upstash)

- RQ job queue
- Rate-limit token buckets (5 scans/IP/hour)
- Short-TTL cache for GitHub API responses (60s)
- Free tier (10k commands/day) fine for MVP

### Object storage — Cloudflare R2

- Stores raw tool outputs per scan: `s3://stackhealth/scans/<scan_id>/{scorecard,semgrep,trivy,cloc}.json`
- Publicly readable (transparency principle)
- No egress fees, $0.015/GB storage

---

## Data flow: a scan, end to end

1. **User submits** `https://github.com/owner/repo` on the landing page.
2. Next.js client POSTs `/api/scans` with `{ repo_url }`.
3. API:
   - Validates URL is github.com/{owner}/{name}
   - Hits `GET https://api.github.com/repos/owner/repo` to confirm: exists, public, not archived/disabled
   - Looks up or inserts a `Repo` row
   - Inserts a `Scan` row with `status="queued"`
   - Enqueues `run_scan(scan_id)` to RQ
   - Returns `{ scan_id }` (HTTP 202 Accepted)
4. Client redirects to `/scan/:scan_id`.
5. Page polls `GET /api/scans/:scan_id` every 2s. API just reads the row and returns status + completed-engine list.
6. **Worker picks up the job:**
   - Update status to `cloning`. Shallow `git clone --depth 1` into an ephemeral container tmpdir.
   - Update to `analyzing`. Spawn 4 subprocesses in parallel:
     - `scorecard --repo=github.com/owner/repo --format=json`
     - `semgrep --config=p/security-audit --json /repo`
     - `trivy fs --format json /repo`
     - `cloc --json /repo` (+ runs `radon`, `ruff`/`eslint`, `jscpd`, `lizard`)
   - Update completed-engines list as each finishes.
   - Fetch GitHub metadata (stars, last_commit_at, contributors, issue stats) via API.
   - Compute formula → `security_score`, `quality_score`, `hygiene_score`, `community_score`, `overall_score`, `grade`.
   - Write `ScanFinding` rows for each issue.
   - Upload raw JSONs to R2.
   - Update `Scan.status = "complete"`, populate score columns.
   - Delete the tmpdir.
7. Client poll sees `status="complete"`, redirects to `/r/owner/repo/scan_id`.

### Failure modes

- **Repo not found / private:** API returns 404 immediately, never enqueues.
- **Clone times out (>30s):** Worker marks scan `failed` with reason `clone_timeout`.
- **Engine crashes:** Worker logs, marks that sub-score as null, continues with others. Overall score is computed from remaining engines with proportional reweighting, flagged as `partial=true` on the report.
- **All engines crash:** Worker marks scan `failed` with reason `engines_failed`. User sees a "try again" page.
- **Worker dies mid-scan:** RQ requeues; scan resumes from scratch on next worker.

---

## Why this shape, and not simpler / different

| Alternative | Why we didn't pick it |
|-------------|----------------------|
| Sync API (no queue) | A 90s HTTP request behind Vercel/Cloudflare will time out. Queue is required. |
| Lambdas per engine | Cold starts + 15-min limits awkward for Semgrep on big repos. Long-running container worker is simpler. |
| GitHub Actions as the worker | Tempting (free compute), but coupling product uptime to Actions queue is risky. |
| Postgres-only (no Redis) | Possible (use `pg_listen`), but RQ + Upstash is more idiomatic and free. |
| Self-host Postgres | Operational burden. Neon free tier is enough. |
| Build our own static analysis | Wildly out of scope. We aggregate. |

---

## Scale envelope

This architecture is comfortable up to:

- **1,000 scans/day** on a single worker (rate-limited by per-scan time)
- **100 GB** raw outputs/year (well within R2 free tier)
- **10 concurrent users** browsing reports (Vercel handles this trivially)

When we exceed it (good problem), the easy levers are:
- Scale workers horizontally on Fly.io (`fly scale count 3`)
- Move to Upstash paid tier ($10/month)
- Move to Neon paid tier ($19/month, gives 10 GB + autoscaling)

Bigger scale (10k scans/day) would warrant:
- Sharding worker pools by language (Semgrep is much slower on big JS/TS repos)
- Aggressive result caching: if same commit SHA, return cached scan
- Moving R2 to a CDN-fronted bucket for faster artifact loads
