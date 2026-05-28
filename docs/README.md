# StackHealth

> A free, transparent, open-formula benchmark for the health of any public code repository.

Paste a GitHub URL. Get a score. Share the report. Discuss it with your peers.

That's it.

---

## What lives in this folder

This folder is the planning home for StackHealth — the place where every decision, formula, and timeline is written down before code is written. Read these in order if you're new:

| # | File | What it covers |
|---|------|----------------|
| 00 | `README.md` | This file. Start here. |
| 01 | `01-VISION.md` | Why StackHealth exists and the principles it will be built on |
| 02 | `02-PRODUCT-SPEC.md` | What the product does — features, user flows, screens |
| 03 | `03-SCORING-METHODOLOGY.md` | **The open formula.** The most important file. |
| 04 | `04-ARCHITECTURE.md` | High-level system design and data flow |
| 05 | `05-TECH-STACK.md` | Stack decisions and why each piece was chosen |
| 06 | `06-ROADMAP.md` | 12-week phased plan from MVP to a real product |
| 07 | `07-MVP-BUILD-PLAN.md` | Week-by-week, day-by-day build plan for the first 4 weeks |
| 08 | `08-DATA-MODEL.md` | Postgres schema and entity-relationship diagram |
| 09 | `09-API-DESIGN.md` | FastAPI endpoint specifications |
| 10 | `10-FRONTEND-PAGES.md` | Next.js page list, components, design notes |
| 11 | `11-INFRASTRUCTURE-AND-COSTS.md` | Hosting, CI/CD, monthly cost estimate |
| 12 | `12-SECURITY-AND-PRIVACY.md` | What we store, what we don't, sandboxing model |
| 13 | `13-LAUNCH-AND-GROWTH.md` | Solo-builder GTM, distribution channels, 90-day goals |
| 14 | `14-COMPETITORS.md` | CodeFactor, SonarCloud, DeepSource, Codacy, OpenSSF — and where StackHealth differs |
| -- | `TODO.md` | Live action items. Update as you go. |

---

## The one-line pitch

> StackHealth is the open standard for code health — like Lighthouse for websites, but for any GitHub repo, with a fully transparent formula anyone can read, fork, or argue with.

---

## The four scoring dimensions (full detail in `03-SCORING-METHODOLOGY.md`)

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Security | 30% | OpenSSF Scorecard + Semgrep + dependency CVEs |
| Quality | 25% | Lint density, complexity, duplication, test signals |
| Hygiene | 25% | README, LICENSE, CONTRIBUTING, CI, tests, recent activity |
| Community | 20% | Stars, contributors, issue response, activity |

**Overall = weighted average → letter grade (A+ to F).** Every input is shown on the report page. Every weight is in a versioned spec file. If you disagree with the formula, you can read it, propose a change, or compute your own from the raw outputs we publish.

---

## The four commitments

1. **Free for public repositories. Forever.**
2. **The formula is public.** Versioned, documented, criticizable.
3. **Reports are shareable.** Permalinks, badge SVGs, embed everywhere.
4. **Raw outputs are visible.** No black box. Click through to the Semgrep findings, the Scorecard JSON, the cloc table.

---

## Status

Planning. Code not started. Target MVP launch: **4 weeks from kickoff.**

Update `TODO.md` after every working session.
