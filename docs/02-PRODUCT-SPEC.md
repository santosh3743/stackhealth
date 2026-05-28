# 02 — Product Specification

## The whole product in one paragraph

A visitor lands on `stackhealth.dev`. The page is a single big input that says "Paste a GitHub URL." They paste, hit Scan. A progress page shows the four engines running. Within ~90 seconds they land on a report page: one giant letter grade, four sub-scores in cards, a stack of expandable finding sections, a "Methodology" tab explaining how the score was computed, a Share button with a permalink and a `![](badge.svg)` snippet, and a Discuss button below the fold. The URL of the report is permanent and public.

---

## User flows

### Flow 1: First scan (anonymous, 0–90 seconds)

1. Land on `/` → see big URL input + sample report links.
2. Paste `https://github.com/owner/repo` → click **Scan**.
3. Client-side validation: must be a valid GitHub URL pointing to a public repo (`HEAD` check against the GitHub API).
4. POST to `/api/scans` → returns `{ scan_id, status: "queued" }`.
5. Redirect to `/scan/:scan_id`.
6. Page polls `/api/scans/:scan_id` every 2 seconds, showing live status: `queued → cloning → analyzing (3/4 engines done) → scoring → complete`.
7. On `complete`, redirect to `/r/:owner/:name/:scan_id`.

### Flow 2: Viewing a report

1. Hero: huge letter grade circle (A+, A, A-, B+, …, F), numeric score, repo name, scanned-at timestamp, formula version badge.
2. Four sub-score cards: Security, Quality, Hygiene, Community. Each shows a numeric score and a one-line summary.
3. **Findings sections** (collapsed by default, expandable):
   - Security findings (severity-grouped, click to see raw Semgrep output)
   - Quality findings (top complex files, lint density per language, duplication)
   - Hygiene checklist (README ✓, LICENSE ✓, CONTRIBUTING ✗, CI ✓, tests/ dir ✓, recent commit ✓)
   - Community signals (contributors, last commit, issue response time, stars)
4. **"How is this scored?"** tab → renders `03-SCORING-METHODOLOGY.md` with the actual values for this scan substituted in.
5. **Raw artifacts** drawer → links to the unprocessed JSON outputs (OpenSSF Scorecard JSON, Semgrep JSON, cloc table). Hosted on R2 with public read.
6. **Share** → permalink + badge SVG + Twitter/X intent link.
7. **Discuss** (Phase 3) → threaded comments below.

### Flow 3: Re-scanning

- Anyone can re-trigger a scan on any repo. New scan_id, new permalink.
- A repo page (`/r/:owner/:name`) shows a small timeline of all scans with score deltas.
- Rate limit: 5 scans / IP / hour anonymous; 1 scan / repo / hour globally.

### Flow 4: Discover

- `/discover` — recent scans (last 24h), trending (most-viewed reports in 7d).
- `/leaderboard?language=python` — top 50 Python repos by Overall score (min 100 stars to qualify, to prevent gaming).

### Flow 5: Embedding the badge

- On any report page, "Embed" reveals:
  ```markdown
  [![StackHealth](https://stackhealth.dev/r/owner/repo/badge.svg)](https://stackhealth.dev/r/owner/repo)
  ```
- The badge SVG is served dynamically. It always shows the **latest** scan score for that repo (cached 1h).
- Badge styles: `flat` (default), `for-the-badge`, `social`.

---

## Page list (MVP)

| Route | Purpose | Phase |
|-------|---------|-------|
| `/` | Landing + URL input | 1 |
| `/scan/:scan_id` | Live progress | 1 |
| `/r/:owner/:name` | Latest report for a repo | 1 |
| `/r/:owner/:name/:scan_id` | Specific historical scan | 1 |
| `/r/:owner/:name/badge.svg` | Embeddable badge | 1 |
| `/methodology` | The open formula doc | 1 |
| `/about` | Vision, FAQ, contact | 1 |
| `/discover` | Recent + trending scans | 2 |
| `/leaderboard` | Top repos by language | 2 |
| `/compare?a=…&b=…` | Side-by-side two repos | 2 |
| `/api/docs` | Public API documentation | 2 |

Full Next.js page spec lives in `10-FRONTEND-PAGES.md`.

---

## Feature scope by phase

### Phase 1 — MVP (Weeks 1–4)

**Goal:** A working, public, anonymous "paste URL → get score → share permalink" loop.

- Landing page with URL input + 3 sample reports.
- Scan submission, queued analysis, live progress page.
- All four scoring engines wired up.
- Report page with overall grade, sub-scores, expandable findings, raw artifact links.
- Permalinks and badge SVG.
- Methodology page (renders `03-SCORING-METHODOLOGY.md` as docs).
- Anonymous rate limiting.

**Out of scope for MVP:** Login, comments, leaderboards, compare, discover.

### Phase 2 — Standard (Weeks 5–8)

- `/discover` page with recent + trending.
- `/leaderboard` per-language.
- `/compare` two-repo side-by-side.
- Sharing analytics (badge impressions, report views).
- GitHub OAuth login (optional — lets users "claim" their scans).
- Improved scoring v1.1 based on real-world data.

### Phase 3 — Community (Weeks 9–12)

- Comments and peer review on reports.
- "False positive" marking by repo owners (verified via GitHub OAuth).
- Formula change proposals (GitHub-backed, like RFC process).
- StackHealth GitHub Action that comments scores on PRs.
- Public API (rate-limited) for programmatic use.

### Phase 4 — Scale (Months 4–6, optional)

- Private repos via GitHub App.
- Organization dashboards.
- Webhooks (notify on score change).
- Paid tier (private repos, org dashboards, API quotas).
- Self-hosted offering.

---

## Non-goals (worth re-stating)

- We will not build our own static analysis rules. We wrap proven OSS tools.
- We will not generate prose feedback or AI suggestions in MVP.
- We will not store source code beyond the scan job.
- We will not become a code-search or code-browsing product.

---

## Trust and credibility checklist

For StackHealth to become a "standard" people cite, it must look and behave like a serious project from day one:

- Public methodology page is fully written before launch
- Status page (`status.stackhealth.dev`)
- Public changelog
- Open-source repository for the formula spec (not necessarily the whole app)
- Privacy and security pages clearly listing what is and isn't stored
- No dark patterns: no "sign up to see results", no upsell modals in MVP
