# 07 — MVP Build Plan (Weeks 1–4)

> A day-by-day, weekend-by-weekend plan to ship the StackHealth MVP in four weeks of solo evenings + weekend hours (~10 hours/week, ~40 hours total). If you have more time, finish faster. If less, slip to 6 weeks — but don't slip past 6.

Every task should be commit-able in one sitting (1–2 hours). If a task feels bigger, split it.

---

## Week 1 — Skeleton (the "hello world" week)

**Goal at end of Week 1:** Landing page deployed at stackhealth.dev. Submitting a URL inserts a `Scan` row in production Postgres and returns a scan_id. No actual scoring yet.

### Mon evening — Setup (2h)
- [ ] `pnpm create next-app apps/web --typescript --tailwind --app`
- [ ] `uv init apps/api`, add FastAPI + SQLAlchemy + Alembic + Pydantic to `pyproject.toml`
- [ ] Create `infra/Dockerfile`, `infra/fly.api.toml`, `infra/fly.worker.toml`
- [ ] Push to `stackhealth-dev/stackhealth` GitHub repo
- [ ] Buy + DNS the `stackhealth.dev` domain

### Tue evening — Deploy hello world (2h)
- [ ] `fly launch` for API → returns Hello from `/`
- [ ] Connect Vercel to GitHub repo → Next.js deploys
- [ ] Point `stackhealth.dev` DNS to Vercel, `api.stackhealth.dev` to Fly
- [ ] Verify both load over HTTPS

### Wed evening — Database setup (2h)
- [ ] Create Neon project + production branch + staging branch
- [ ] Add `DATABASE_URL` to Fly secrets
- [ ] Initialise Alembic
- [ ] Write the schema from `08-DATA-MODEL.md`:
  - `repos`, `scans`, `scan_findings`, `formula_versions`
- [ ] Run migration in production

### Sat morning — Landing page UI (3h)
- [ ] Hero with big URL input
- [ ] Three sample report stubs ("see how `expressjs/express` scored")
- [ ] About section explaining the formula at a glance
- [ ] Footer: GitHub link, methodology link, status link
- [ ] Use shadcn/ui `Button`, `Input`, `Card`

### Sun morning — Scan submission API (3h)
- [ ] `POST /api/scans` — validates GitHub URL, calls GitHub API to confirm public repo, inserts Repo + Scan rows, returns `{ scan_id }`
- [ ] `GET /api/scans/:id` — returns scan row
- [ ] Wire frontend form to API, redirect to `/scan/:id` on success
- [ ] `/scan/:id` page with a fake "scanning..." spinner that just polls
- [ ] Deploy and test end-to-end in production

**Week 1 deliverable:** `stackhealth.dev` lets you submit a URL. Database stores it. The progress page polls and shows "queued forever" because no worker yet. **That's fine.**

---

## Week 2 — Scoring pipeline part 1 (worker + first engine)

**Goal at end of Week 2:** Worker process running. Submitting a URL actually computes a Hygiene score and writes it to the DB. Progress page updates in real time.

### Mon evening — Redis + RQ (2h)
- [ ] Provision Upstash Redis, add `REDIS_URL` to Fly secrets
- [ ] Add `rq` to `pyproject.toml`
- [ ] Create `apps/api/stackhealth/worker/__init__.py` with a sample `add(x, y)` job
- [ ] `fly deploy` a second app from the same image as the worker (`fly.worker.toml`, just changes the CMD)
- [ ] Test: from API, enqueue `add(2, 2)`; worker logs show it ran

### Tue evening — Scan job skeleton (2h)
- [ ] `worker/jobs.py:run_scan(scan_id)` updates status to `cloning` → fakes a 5s sleep → updates to `analyzing` → 5s sleep → `complete`
- [ ] `POST /api/scans` enqueues `run_scan`
- [ ] Frontend poll now sees real status transitions
- [ ] Status enum: `queued`, `cloning`, `analyzing`, `scoring`, `complete`, `failed`

### Wed evening — Git clone helper (2h)
- [ ] Install `git` in Fly worker Dockerfile
- [ ] `engines/clone.py` — shallow clone, timeout 30s, ephemeral tmpdir, cleanup on exit
- [ ] Capture commit SHA, write to `Scan.commit_sha`

### Sat morning — GitHub metadata fetcher (3h)
- [ ] `engines/github_meta.py` — fetch repo, stars, contributors, issues from GitHub REST
- [ ] Handle rate limits (use a personal access token in Fly secrets — 5k req/hour)
- [ ] Store: stars, forks, last_commit_at, contributor_count, language, license

### Sun morning — Hygiene engine + first score (3h)
- [ ] `engines/hygiene.py` — runs the binary checklist from `03-SCORING-METHODOLOGY.md` §3
  - Read filesystem after clone for README.md, LICENSE, CONTRIBUTING.md, etc.
  - Parse `.github/workflows/*.yml` for `on: pull_request`
- [ ] `formula/v1.py:compute_hygiene(checklist) -> int`
- [ ] Update `Scan.hygiene_score` at end of `run_scan`
- [ ] `/r/:owner/:name/:scan_id` page renders just the Hygiene score for now
- [ ] Deploy, scan a real repo, see a real score

**Week 2 deliverable:** End-to-end works. Hygiene score is real. Report page shows one number. Worker actually runs.

---

## Week 3 — Scoring pipeline part 2 (the heavy engines)

**Goal at end of Week 3:** All four sub-scores computed and displayed on a real report page.

### Mon evening — OpenSSF Scorecard integration (2h)
- [ ] `engines/scorecard.py` — first try `GET https://api.scorecard.dev/projects/github.com/{owner}/{name}`
- [ ] If 404: run `scorecard` binary locally (install in worker Dockerfile)
- [ ] Parse JSON, extract aggregate score, store raw output to R2
- [ ] Wire into `run_scan`

### Tue evening — Semgrep integration (2h)
- [ ] Add `semgrep` to worker Docker image
- [ ] `engines/semgrep.py` — run `semgrep --config=p/security-audit --json /repo --timeout 60`
- [ ] Parse findings, count by severity
- [ ] Upload raw JSON to R2
- [ ] Compute LoC-normalised security_score per formula §1b

### Wed evening — Trivy + cloc (2h)
- [ ] Add `trivy` + `cloc` to worker Docker image
- [ ] `engines/trivy.py` — `trivy fs --format json --severity HIGH,CRITICAL /repo`
- [ ] `engines/cloc.py` — `cloc --json /repo`, store LoC by language
- [ ] Compute dependency_score per formula §1c

### Thu evening — Quality engines (2h)
- [ ] `engines/lint.py` — language detection from cloc, dispatch to:
  - Python: `ruff check --output-format=json`
  - JS/TS: `eslint --format=json` (if `.eslintrc*` present, else skip)
  - Go: `golangci-lint run --out-format=json` (if `go.mod` present)
- [ ] `engines/complexity.py` — `lizard --csv` (multi-language)
- [ ] `engines/dup.py` — `jscpd --reporters json`
- [ ] Compute quality_score per formula §2

### Sat morning — Formula integration + full scan (3h)
- [ ] `formula/v1.py:compute_overall(security, quality, hygiene, community) -> (score, grade)`
- [ ] Compute community_score per formula §4
- [ ] End-to-end: scan a known repo, verify each sub-score makes sense
- [ ] Fix obvious calibration issues

### Sun morning — Report page UI (3h)
- [ ] Hero with letter grade circle + overall score + repo name
- [ ] 4 sub-score cards (Security, Quality, Hygiene, Community)
- [ ] Collapsible findings sections (Accordion)
- [ ] "Raw artifacts" drawer with links to R2 JSON URLs
- [ ] Use ISR: `revalidate: 3600`, on-demand revalidation when new scan completes
- [ ] Run scans on 10 different repos to stress-test UI

**Week 3 deliverable:** Submit any public GitHub URL → ~90 seconds later, see a real composite score with four sub-scores and clickable raw outputs.

---

## Week 4 — Polish, share, launch

**Goal at end of Week 4:** Public launch on Product Hunt + Hacker News.

### Mon evening — Badge SVG (2h)
- [ ] `GET /r/:owner/:name/badge.svg` — server-rendered SVG with grade + score, cached 1h
- [ ] Styles: `flat` (default), `for-the-badge`
- [ ] Embed snippet on report page (copy-to-clipboard)

### Tue evening — Methodology page (2h)
- [ ] `/methodology` renders `03-SCORING-METHODOLOGY.md` (use `next-mdx-remote`)
- [ ] Side-anchor nav for sections
- [ ] Link to `stackhealth-dev/formula` repo

### Wed evening — Share modal (2h)
- [ ] Share button on report page
- [ ] Modal: permalink copy, badge embed code, Twitter/X intent link
- [ ] OG image generation for report pages (`opengraph-image.tsx`) — score + grade

### Thu evening — Rate limiting + abuse (2h)
- [ ] Redis-backed token bucket: 5 scans/IP/hour anonymous
- [ ] 1 scan/repo/hour globally
- [ ] CAPTCHA fallback if abuse spikes (Cloudflare Turnstile, free)

### Sat morning — Sample reports + landing polish (3h)
- [ ] Pre-run scans on 3 hero repos: a good one (`fastapi/fastapi`), a tiny one, a fun one
- [ ] Link them prominently on landing
- [ ] Tighten landing copy
- [ ] Add `/about` and `/methodology` to header nav
- [ ] Add Plausible analytics
- [ ] Add Sentry to API + worker

### Sat afternoon — Status page (1h)
- [ ] Simple `status.stackhealth.dev` (Better Stack free tier or self-build)
- [ ] Public uptime numbers from day 1

### Sun morning — Launch prep (3h)
- [ ] Product Hunt page drafted (title, tagline, gallery images)
- [ ] HN Show post drafted
- [ ] Tweet thread drafted
- [ ] dev.to post drafted: "I built an open-formula code health score in 4 weeks"
- [ ] Outreach list: 10 OSS maintainers whose repos you've scanned to ask for feedback

### Sun evening — Launch (1h)
- [ ] Submit Product Hunt for next-day launch
- [ ] Post HN Show
- [ ] Tweet
- [ ] Post in r/programming, r/opensource
- [ ] Reply to every comment for 48h

**Week 4 deliverable:** StackHealth is live, public, talked about. You're answering comments on three platforms simultaneously. You have actual users.

---

## Risks and how to handle them

| Risk | Mitigation |
|------|-----------|
| Semgrep is too slow on big repos | Set 60s timeout. If timed out, score that engine as null with `partial=true` |
| GitHub API rate limit hit | Cache responses for 60s; on 429, queue retry with exponential backoff |
| Worker crashes mid-scan | RQ requeues; idempotent job design (delete partial scan record on retry) |
| Spam scans | Rate limit + Cloudflare in front + CAPTCHA on abuse |
| Repo too big to clone in 30s | Hard timeout; mark scan failed with reason; show "this repo is too large" to user |
| Formula gives nonsensical scores | Run on 20 known-good and 20 known-bad repos before launch; tweak thresholds |
| Vercel/Fly bill surprises | Set Plausible alerts on traffic; set Fly machine count caps; review weekly |

---

## "I have more time" stretch goals for Week 4

If you ship Week 4 deliverables early:
- Pre-generate 100 high-quality reports on famous OSS repos so the discover page isn't empty at launch
- Write the first formula-evolution RFC ("v1.1: planned changes")
- Build the GitHub Action (originally Phase 3) — would be a launch differentiator
