# 10 — Frontend Pages

> Next.js App Router pages, components, and the visual design language.

## Visual identity

- **Primary color:** Indigo 600 (`#4f46e5`) — confident, trustworthy
- **Grade colors:**
  - A+/A → emerald 500
  - A-/B+ → green 500
  - B/B- → yellow 500
  - C+/C/C- → orange 500
  - D → red 500
  - F → rose 700
- **Typography:**
  - Headings: Inter, bold, tight tracking
  - Body: Inter, regular
  - Mono (for code): JetBrains Mono
- **Vibe:** Lighthouse meets GitHub. Clean, technical, not enterprise-looking. Lots of whitespace. Big numbers.
- **Dark mode:** From day one. Auto-detect + toggle.

---

## Page-by-page spec

### `/` — Landing

```
┌──────────────────────────────────────────────────────┐
│  StackHealth                  Methodology  About  GH │
├──────────────────────────────────────────────────────┤
│                                                       │
│      The open code health benchmark                   │
│      Score any public repo. Share it. Open formula.   │
│                                                       │
│   ┌──────────────────────────────────────┐ ┌──────┐  │
│   │ https://github.com/owner/repo        │ │ Scan │  │
│   └──────────────────────────────────────┘ └──────┘  │
│                                                       │
│   12,483 repos scanned · v1.0 formula · open source   │
│                                                       │
├──────────────────────────────────────────────────────┤
│  Try a sample                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                  │
│  │   A-    │ │   B+    │ │   F     │                  │
│  │ fastapi │ │ flask   │ │ left-pad│                  │
│  └─────────┘ └─────────┘ └─────────┘                  │
├──────────────────────────────────────────────────────┤
│  How it works                                          │
│  1. Paste a URL  2. We score  3. You share            │
│                                                       │
│  Four dimensions: Security · Quality · Hygiene · Community │
└──────────────────────────────────────────────────────┘
```

Server component. SEO-critical. Sample reports are real, pre-computed scans linked from constants.

### `/scan/:scan_id` — Live progress

```
┌──────────────────────────────────────────────────────┐
│  Scanning github.com/owner/repo                       │
│                                                       │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░  Analyzing…                       │
│                                                       │
│  ✓ Cloned                                             │
│  ✓ Scorecard                                          │
│  ✓ Hygiene                                            │
│  ⟳ Semgrep                                            │
│  ⟳ Trivy                                              │
│  ○ Lint + complexity                                  │
│                                                       │
│  Typically 60–120 seconds.                            │
└──────────────────────────────────────────────────────┘
```

Client component. Polls `/api/scans/:id` every 2s. Streaming UI via Suspense.

### `/r/:owner/:name` — Latest report (canonical)

Redirects (via 302) to `/r/:owner/:name/:latest_scan_id` so the URL is stable but shareable as latest.

Also: `<link rel="canonical">` set correctly so SEO doesn't get confused.

### `/r/:owner/:name/:scan_id` — Report

```
┌──────────────────────────────────────────────────────┐
│  fastapi / fastapi                       Share ▾ Re-scan │
│  Python · MIT · 78k stars · last commit 2 days ago    │
├──────────────────────────────────────────────────────┤
│                                                       │
│              ╭─────────╮                              │
│              │   A-    │     89 / 100                 │
│              ╰─────────╯     Formula v1.0             │
│                                                       │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│   │ Security │ │ Quality  │ │ Hygiene  │ │Community ││
│   │   86     │ │   84     │ │   97     │ │   92     ││
│   │  Strong  │ │  Strong  │ │ Excellent│ │  Strong  ││
│   └──────────┘ └──────────┘ └──────────┘ └──────────┘│
│                                                       │
│  Findings  |  How it's scored  |  Raw artifacts        │
├──────────────────────────────────────────────────────┤
│  ▼ Security · 86                                       │
│      OpenSSF Scorecard: 8.5 / 10                       │
│      Semgrep:  3 high, 12 medium, 24 low               │
│      Dependencies: 0 critical, 2 medium CVEs           │
│      [click any finding to see source]                 │
│                                                       │
│  ▶ Quality · 84                                        │
│  ▶ Hygiene · 97                                        │
│  ▶ Community · 92                                      │
└──────────────────────────────────────────────────────┘
```

Server component with ISR. Data fetched server-side from API. Findings expanded on click via client component.

OG image: a 1200×630 PNG generated by Next.js `opengraph-image.tsx` — score, grade, repo name. Shared on social = beautiful preview.

### `/methodology`

Renders `03-SCORING-METHODOLOGY.md` (via MDX). Anchored ToC sidebar. "View source" link to the formula repo.

### `/about`

Vision + principles (from `01-VISION.md`). Contact email. GitHub link.

### `/discover` (Phase 2)

Tabs: Recent / Trending.

Grid of report cards (grade + score + repo + language + stars).

Pagination ("Load more").

### `/leaderboard` (Phase 2)

Language tabs: Python / JS / TS / Go / Rust / Java / Ruby / others.

Top 50 list per language. Min-stars filter.

### `/compare` (Phase 2)

Two URL inputs at top → side-by-side report layout.

Differences highlighted (green where A is better, red where B is better).

Shareable: `/compare?a=fastapi/fastapi&b=tiangolo/asyncer`.

---

## Components (shadcn/ui-based)

| Component | Purpose |
|-----------|---------|
| `GradeBadge` | The colored letter-grade circle (variants: hero / card / inline) |
| `ScoreCard` | Sub-score card with number + label + qualitative description |
| `FindingItem` | One finding row with severity icon, title, file path, expand-on-click |
| `FindingGroup` | Accordion section grouping findings by engine |
| `ScanProgress` | Stepper UI for live scan progress |
| `BadgeEmbed` | The embed-snippet copy-to-clipboard widget |
| `ShareDialog` | Modal with permalink + badge embed + social share |
| `RepoMeta` | Top-of-report metadata strip (stars, language, license, last commit) |
| `MethodologyToC` | Side-anchor nav for the methodology page |

---

## Loading and empty states

| State | Treatment |
|-------|-----------|
| Scan submitted, no data yet | Stepper with all steps pending |
| Scan in progress | Stepper showing live status |
| Scan complete | Full report page |
| Scan failed | Friendly explanation + "try again" button |
| Repo not found | "We can't find that repo. Is it public?" with link to GitHub |
| Repo too large | "This repo exceeds our scan limit. Coming in Pro tier." |
| Rate limited | "Slow down, friend. Try again in N minutes." with humor |
| 404 | Custom 404 page linking back to `/` and recent scans |

---

## Mobile responsiveness

Every page works on mobile (≥ 375px wide):
- Landing: single-column, URL input full-width
- Report: 4 sub-score cards stack 2x2 on tablet, 1x4 on mobile
- Findings: same layout, just narrower
- Tables in raw artifacts: horizontal scroll allowed

---

## Accessibility

- All interactive elements keyboard-navigable
- ARIA labels on grade badges (`aria-label="Grade A-"`)
- Color is never the only signal — letter + word ("Strong") always present
- WCAG AA contrast everywhere
- `prefers-reduced-motion` respected for animations

---

## Performance budgets

| Page | TTFB | LCP | JS bundle |
|------|------|-----|-----------|
| `/` | <200ms | <1.5s | <80KB gzipped |
| `/r/:owner/:name/:scan_id` | <200ms (ISR cached) | <2s | <120KB |
| `/scan/:id` | <300ms | <1.5s | <100KB |

Tested on every PR via `unlighthouse` GitHub Action.
