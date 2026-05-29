# 06 — Roadmap

> The 12-week phased plan from zero to a real, usable, talked-about product. Plus what comes after.

This is a **solo, evenings-and-weekends** roadmap. Effort estimates assume ~10 focused hours per week. If you have more time some weeks, you'll move faster — these are floors, not ceilings.

---

## Phase 0 — Foundations (Week 0, ~6 hours)

The week before code is written.

- [ ] Buy `stackhealth.dev` domain (Namecheap or Porkbun)
- [ ] Register GitHub org `santosh3743` (free)
- [ ] Create three repos: `santosh3743/stackhealth` (app), `santosh3743/stackhealth/tree/main/packages/formula-spec` (spec), `santosh3743/stackhealth/tree/main/docs` (this folder, made public when ready)
- [ ] Sign up: Vercel, Fly.io, Neon, Upstash, Cloudflare R2, Sentry, Plausible
- [ ] Provision: Neon project + branch, Upstash Redis, R2 bucket
- [ ] Create a Linear or GitHub Projects board with the Phase 1 issues from `07-MVP-BUILD-PLAN.md`
- [ ] Logo + brand color (Phase 0, not Phase 5 — having a logo makes the project feel real)

**Deliverable:** All accounts created, all infrastructure provisioned, all repos exist, board has issues.

---

## Phase 1 — MVP (Weeks 1–4)

**Goal:** A live, public, working "paste URL → get score → share permalink" product.

Detailed week-by-week plan: see `07-MVP-BUILD-PLAN.md`.

### Week 1 — Skeleton
Next.js app deployed, FastAPI deployed, DB schema migrated, "Hello world" e2e.

### Week 2 — Scoring pipeline (1/2)
Worker plumbing, OpenSSF Scorecard integration, GitHub metadata, Hygiene score.

### Week 3 — Scoring pipeline (2/2)
Semgrep, Trivy, cloc + lint, full formula, report page UI.

### Week 4 — Polish + launch
Badge SVG, share modal, methodology page, sample reports, beta launch.

**Phase 1 deliverable:** `stackhealth.dev` is live. You can paste a URL, get a score, share the permalink, embed the badge. Methodology page is published. Three "hero" sample reports are linked from the landing page (a popular repo like `expressjs/express`, a small good one, and a hilariously bad one).

**Phase 1 success metrics (4 weeks post-launch):**
- 100 unique repos scanned
- 50 GitHub stars on the `santosh3743/stackhealth` repo
- 1 mention on Hacker News, dev.to, or X with >100 likes/upvotes

---

## Phase 2 — Standard (Weeks 5–8)

**Goal:** Make StackHealth feel like a benchmark, not a one-off tool.

### Week 5 — Discover + recent activity
- `/discover` page: recent scans + most-viewed in 7d
- Cron job to maintain trending list
- Sitemap with all public report URLs (SEO)

### Week 6 — Leaderboard by language
- `/leaderboard?language=python|js|go|rust|...`
- Min 100 stars to qualify (prevent gaming)
- One-month rolling re-scan of all leaderboard entries

### Week 7 — Compare two repos
- `/compare?a=…&b=…` side-by-side
- Useful for "which of these two libraries should I pick?"
- Shareable URL with both repos baked in

### Week 8 — GitHub OAuth + scoring v1.1
- Optional GitHub login: claim your scans, get notified on score change
- Iterate the formula based on data — publish `v1.1` with calibration tweaks
- Public RFC process for changes

**Phase 2 deliverable:** Discover, leaderboard, compare all live. Formula v1.1 published with public changelog. A few maintainers have claimed their repos.

**Phase 2 success metrics (8 weeks post-launch):**
- 1,000 scans
- 200 GitHub stars
- 20 embedded badges on real READMEs (measurable via badge SVG referrer logs)

---

## Phase 3 — Community (Weeks 9–12)

**Goal:** Turn the benchmark into a community.

### Week 9 — Comments & peer review
- Auth-gated comments on report pages
- "False positive" marking by verified repo owners
- Comment moderation queue

### Week 10 — Formula RFC system
- A `proposals/` directory in the `formula` repo
- A web UI showing open proposals + voting
- Quarterly formula version bumps

### Week 11 — GitHub Action
- `stackhealth/scan-action@v1` — runs in CI, comments score on PRs
- Score delta vs. main: "This PR moves your score from B+ to B-"
- Distribution: each install is a new READM mention

### Week 12 — Public API + docs
- `/api/v1/scans`, `/api/v1/repos/{owner}/{name}`, `/api/v1/leaderboard`
- API key auth (free tier: 100 req/hour)
- Public API docs at `/api/docs`

**Phase 3 deliverable:** A breathing community. People are arguing on report pages. Pull requests are coming in to the formula repo. The GitHub Action has been installed on a few dozen repos.

**Phase 3 success metrics (12 weeks post-launch):**
- 5,000 scans
- 500 GitHub stars
- 5 community-authored formula RFCs (closed or open)
- 100 GitHub Action installations

---

## Phase 4 — Scale (Months 4–6, optional)

Only if Phase 1–3 have product-market fit signals.

### Private repos (GitHub App)
- Install the StackHealth GitHub App on your org → private repos are scannable
- Org dashboard at `/org/:slug`
- All private results stay private

### Organization dashboards
- Roll-up score across all org repos
- Trends over time
- Compare your team to industry benchmarks (using public-repo data, anonymized)

### Webhooks
- Notify Slack/Discord/email when a repo's score changes
- Trigger on new scans

### Paid tier
- **Free forever:** All public-repo scanning, badges, embeds, basic API.
- **Pro ($9/month):** Private repos (up to 10), priority queue, advanced API quota.
- **Team ($29/month):** Org dashboard, unlimited private repos, webhooks, SSO.
- **Enterprise (custom):** Self-hosted, audit logs, custom rule packs.

Pricing is set so a developer can pay for Pro out of pocket. We are not optimizing for ACV.

---

## Phase 5+ — What "great" looks like a year out

Aspirations, not commitments:

- **`stackhealth.dev/owner/repo` is a URL pattern people share casually**, the way `caniuse.com` URLs are.
- **The formula is cited in academic papers** about OSS health.
- **One major language ecosystem (Python, Go, Rust) recommends StackHealth in its packaging guide.**
- **A conference talk** by you at PyCon / GopherCon / FOSDEM about how the formula was designed.
- **Self-hosted enterprise deployments** at 3-5 companies. Not as a hobby — as a real, paid product line.

---

## What to drop if behind schedule

Roadmaps slip. If by end of Week 4 the MVP isn't live, here's the priority order of what to cut:

1. **Cut first:** Trivy dependency scoring (skip until v1.1, only 6% of overall score)
2. **Cut next:** Multi-language linter (start with Python + JS only)
3. **Cut next:** Custom Quality metrics (just use Scorecard + Hygiene for v0)
4. **Never cut:** The landing page, scan flow, report page, badge SVG. These four make the product real.

Ship something embarrassingly simple by Week 4. Iterate publicly.
