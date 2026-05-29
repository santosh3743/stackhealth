# TODO — Live action list

> The single source of truth for what to do next. Update at the end of every working session.

Format: `[ ] description (estimated hours)`. Move done items into the "Done" section at the bottom with the date.

---

## This week (Week 0 — Foundations)

- [x] Bought `stackhealth.dev` ($12.20/yr) ✅
- [x] Repo at `github.com/santosh3743/stackhealth` (single-repo strategy) ✅
- [ ] Provision the Oracle Cloud Always Free ARM VM and point DNS at it
- [ ] First deploy via `./infra/deploy.sh` and verify Let's Encrypt cert issues
- [ ] Sketch a logo (paper or Figma free tier) — even a basic wordmark works
- [ ] Tweet/post: "Starting a side project — StackHealth, an open code health benchmark. Updates weekly." Start the build-in-public loop.

---

## Week 1 — Skeleton (~10 hours)

See `07-MVP-BUILD-PLAN.md` for the day-by-day breakdown. Top-level:

- [ ] Mon: Project scaffolding (Next.js + FastAPI repos)
- [ ] Tue: First deploy to Vercel + Fly.io
- [ ] Wed: Database schema + migrations
- [ ] Sat: Landing page UI
- [ ] Sun: Scan submission endpoint + progress page polling

---

## Week 2 — Scoring pipeline 1/2 (~10 hours)

- [ ] Mon: Redis + RQ wiring
- [ ] Tue: Scan job skeleton
- [ ] Wed: Git clone helper
- [ ] Sat: GitHub metadata fetcher
- [ ] Sun: Hygiene engine + first real score

---

## Week 3 — Scoring pipeline 2/2 (~10 hours)

- [ ] Mon: OpenSSF Scorecard
- [ ] Tue: Semgrep
- [ ] Wed: Trivy + cloc
- [ ] Thu: Quality engines (lint, complexity, dup)
- [ ] Sat: Formula integration + full scan
- [ ] Sun: Report page UI

---

## Week 4 — Polish + launch (~10 hours)

- [ ] Mon: Badge SVG
- [ ] Tue: Methodology page
- [ ] Wed: Share modal + OG images
- [ ] Thu: Rate limiting
- [ ] Sat AM: Landing polish + sample reports
- [ ] Sat PM: Status page
- [ ] Sun AM: Launch prep (PH, HN, tweets, blog)
- [ ] **Sun PM: LAUNCH**

---

## Open questions / decisions to make

- [ ] Logo — design it yourself or hire on Fiverr ($50)?
- [ ] Should we open-source the entire app, or just the formula repo + spec?
- [ ] Domain: stackhealth.dev vs .io vs .org — what's available?
- [ ] Move docs to a hosted platform (Mintlify, GitBook) or self-host with Next.js?
- [ ] Do we want a Discord/community space from launch, or wait?

---

## Stretch items (post-launch, no deadline)

- [ ] Pre-scan top 100 OSS repos by language for the leaderboard
- [ ] Write a "v1.1 RFC" first formula change before anyone asks
- [ ] Reach out to OpenSSF maintainer to coordinate on co-promotion
- [ ] Submit a lightning-talk proposal for the next reachable conference
- [ ] Set up Fathom / Plausible weekly digest emails

---

## Done

(Move items here with date when finished. Keeps motivation visible.)

- [x] 2026-05-28 — Planning folder created with all 15 docs ✅
- [x] 2026-05-28 — Week 1 skeleton: API routes, DB schema, migration applied, Next.js pages ✅
- [x] 2026-05-28 — Week 2 worker pipeline: shallow clone, RQ enqueue, scan persistence ✅
- [x] 2026-05-28 — Week 3 engines: cloc, semgrep, trivy, scorecard (API+binary), lint dispatch, lizard complexity, jscpd duplication, test-signal heuristic, community sub-scores ✅
- [x] 2026-05-28 — Week 3 report page UI: GradeBadge hero, 4 sub-score cards, breakdown table, findings accordion, reproducibility section, badge embed snippet ✅
- [x] 2026-05-28 — Week 4 polish: methodology page rewrite, badge SVG endpoint working, rate limiting active ✅
- [x] 2026-05-28 — Local dev: docker reuse (zeron-postgres + zeron-redis), .env.local files, scripts/dev.sh ✅
- [x] 2026-05-28 — End-to-end verified: pallets/click scanned to 71 (B-), partial=true correctly flags missing local tools ✅

---

## Notes / scratch

- Domain availability check: do `stackhealth.dev`, `.io`, `.org` first. Settle for `getstackhealth.dev` only as a last resort.
- The formula spec at `packages/formula-spec/` is the credibility anchor — keep it readable and obvious.
- Don't skip the Methodology page — it IS the marketing.
