# 14 — Competitors and Positioning

> An honest, current map of the space. Don't dismiss competitors — learn from them and articulate clearly where StackHealth fits.

## The landscape, in one table

| Tool | Score? | Open formula? | Free for public? | Free for private? | Hosted SaaS? | Composite? |
|------|--------|---------------|------------------|-------------------|--------------|------------|
| **StackHealth** | ✅ A+ to F | ✅ Fully | ✅ Forever | 🔜 Paid tier | ✅ | ✅ |
| CodeFactor.io | ✅ A+ to F | ❌ Closed | ✅ | ❌ Paid | ✅ | ✅ |
| SonarCloud | ✅ A–E | ⚠️ Partial (rules public, weights not) | ✅ | ❌ Paid | ✅ | ✅ |
| Codacy | ✅ A–F | ❌ Closed | ✅ | ❌ Paid | ✅ | ✅ |
| DeepSource | ✅ A–F | ❌ Closed | ✅ | ❌ Paid | ✅ | ✅ |
| Qodana (JetBrains) | ✅ "Quality gate" | ❌ Closed | ✅ (OSS license) | ❌ Paid | ✅ + self-host | ✅ |
| OpenSSF Scorecard | ✅ 0–10 | ✅ Fully open | ✅ | ✅ (run yourself) | ⚠️ scorecard.dev (read-only) | ❌ Security only |
| Snyk Advisor | ✅ Package health 0–100 | ⚠️ Partial | ✅ | ✅ | ✅ | ⚠️ Package-focused |
| GitHub Code Scanning (CodeQL) | ❌ No composite | ❌ Closed | ✅ | ✅ | ✅ | ❌ |
| Sourcegraph Sentinel | ⚠️ Internal scores | ❌ Closed | ❌ | ❌ Enterprise | ✅ | ✅ |
| BetterCodeHub | — | — | — | — | ❌ Discontinued | — |
| Repo Rater (TNS) | ✅ 1–5 stars | ✅ (votes) | ✅ | N/A | ✅ | ⚠️ Vibes-based |

---

## Detailed look at each

### CodeFactor.io — the closest thing to StackHealth today

**What it does:** Paste GitHub URL, get an A+ to F grade. Free for public, paid for private. Per-file issue counts.

**What it does well:**
- Same simplicity we're aiming for
- Letter-grade UI is clear
- Free public-repo coverage is generous

**Where it loses to StackHealth:**
- Formula is closed — you see the score but not why it weighs this over that
- Quality-focused only; minimal security signal
- No public benchmark / leaderboard
- No raw artifact transparency
- Limited share/embed features

**Our edge:** "Open formula. Anyone can read it, fork it, dispute it. Your CodeFactor A is opaque; your StackHealth A is reproducible."

### SonarCloud — the incumbent for serious teams

**What it does:** Industrial-grade static analysis with quality gates, rule customization, and deep IDE integration. Free for public repos with sign-up.

**What it does well:**
- Extensive language coverage
- Established rule packs
- Real CI integration
- Reputation in enterprise

**Where it loses to StackHealth:**
- Onboarding is heavy — must connect repo, configure project, wait for first scan
- The "score" is buried among many metrics; no clean public report
- Anti-viral: requires sign-up just to view results
- Weighting is opaque
- Enterprise vibes turn off OSS maintainers

**Our edge:** "No sign-up. Paste a URL. The benchmark is public — your repo's score is visible to anyone."

### Codacy — middle ground

**What it does:** Hosted SaaS, multi-language, integrates with PRs. Free for OSS, paid for private.

**What it does well:**
- Cleaner UI than SonarCloud
- Decent free tier
- Good PR integration

**Where it loses to StackHealth:**
- Same closed-formula problem
- No public benchmark
- Marketing-heavy upsells

**Our edge:** Same as the others — open formula, no upsell, transparent raw outputs.

### DeepSource — modern challenger

**What it does:** Newer entrant, polished UI, focus on autofix PRs. Free for OSS.

**What it does well:**
- Beautiful UI
- Autofix is a strong wedge feature
- Good developer experience

**Where it loses to StackHealth:**
- Score is incidental, not the focus
- Autofix locks you to their CI
- Closed formula

**Our edge:** "DeepSource is a tool. StackHealth is a benchmark."

### OpenSSF Scorecard — closest in spirit

**What it does:** Fully open, fully transparent security score for public OSS projects. Runs as a CLI or you can fetch results from `api.scorecard.dev`.

**What it does well:**
- Genuinely open (formula, code, results)
- Trusted by big OSS foundations
- Easy to fetch results programmatically

**Where it loses to StackHealth:**
- Security-only — doesn't tell you about code quality
- No web UI for casual lookups (deps.dev embeds it but is not focused)
- No leaderboard, no comparison, no badge culture
- 0–10 scale is harder to share than a letter grade

**Our edge:** "StackHealth includes OpenSSF Scorecard as one of four dimensions. Get the security score AND the quality + hygiene + community picture in one badge."

(In fact: OpenSSF Scorecard is a *dependency* of StackHealth, not a competitor. We should publicly thank them and link to them.)

### Snyk Advisor — package-focused

**What it does:** Free public site at `snyk.io/advisor` that shows a "package health score" for any npm/PyPI/Maven package.

**What it does well:**
- Free, no sign-up
- Composite (combines popularity, maintenance, security, community)
- Good for picking dependencies

**Where it loses to StackHealth:**
- Package-focused, not repo-focused — only works for published packages
- Snyk's commercial intent is obvious
- Formula isn't fully open

**Our edge:** "Snyk Advisor scores packages. StackHealth scores any repo, even ones that aren't published anywhere."

### GitHub Code Scanning (CodeQL)

**What it does:** Free vulnerability scanning integrated into GitHub. Findings show on PRs.

**Where it loses as a competitor:** It's a CI tool, not a score. It's our sibling, not our rival. We can complement it by aggregating its findings into our security score eventually.

---

## How to talk about competitors publicly

We don't trash them. We position:

- **CodeFactor:** "Great free tool. We add the open formula and security signals."
- **SonarCloud:** "The pro option for teams. We're the public benchmark layer."
- **Codacy/DeepSource:** "Strong PR-integration tools. We aggregate. They lint."
- **OpenSSF Scorecard:** "We're built on top of it. It's the gold standard for security." (then link to them)
- **Snyk Advisor:** "For published packages, they're excellent. We extend the score to any repo."

Every competitor mention links to them. Show confidence, not insecurity.

---

## What we can learn from them

| From | Lesson |
|------|--------|
| CodeFactor | UX simplicity. Match it. |
| SonarCloud | Industrial credibility. Borrow patterns (quality gates, but open). |
| Codacy | PR integration matters — build a GitHub Action. |
| DeepSource | UI polish. Don't skimp on visual design. |
| OpenSSF Scorecard | Transparency is the differentiator. Lean into it. |
| Snyk Advisor | Public, no-signup discovery pages are powerful. Build leaderboards. |

---

## The honest answer to "Why does this need to exist?"

Because no current tool combines all of:
1. A single composite score
2. A fully open, versioned formula
3. Free for every public repo
4. Public benchmark pages with raw artifacts
5. Embeddable badge culture
6. Peer-reviewable findings

CodeFactor has 1, 3, 5. SonarCloud has 1, ish 3, 5. Scorecard has 2, 3, 4, 6 but is security-only. Nobody has all six.

That's the wedge. Defend it ruthlessly.
