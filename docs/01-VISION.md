# 01 — Vision

## The problem

Developers, hiring managers, OSS maintainers, and security teams all ask the same question about a codebase: **"Is this any good?"**

The tools that try to answer this today fall into three camps, and none of them is satisfying:

1. **Enterprise SaaS (SonarCloud, Codacy, CodeFactor paid):** Powerful, but the score formulas are proprietary. You see an "A" but not why. Pricing gates the deeper insight behind a paywall.
2. **Single-purpose scanners (OpenSSF Scorecard, Semgrep, Snyk):** Each gives a useful slice — security, dependencies, OSS hygiene — but no single composite score. You have to be technical enough to run them yourself.
3. **Community ratings (Repo Rater, GitHub stars):** Vibes-based. Stars measure popularity, not quality.

The result: there is no widely-trusted, open standard for code health. Lighthouse exists for websites. PageSpeed exists. SSL Labs exists. Code does not have its Lighthouse.

## The vision

**StackHealth is the open standard for code health.**

Anyone can paste a public GitHub URL into a web form and within two minutes receive a single composite score (A+ to F) backed by four sub-scores and dozens of clickable, raw underlying findings. The score is shareable via permalink and an embeddable badge. The formula is published, versioned, and open to community proposal.

In one year, we want a project README that doesn't carry a StackHealth badge to look incomplete — the same way a README without a CI badge looks incomplete today.

## Who it's for

- **OSS maintainers** who want to demonstrate the health of their project
- **Developers evaluating dependencies** who want a faster signal than reading code
- **Hiring managers reviewing candidate portfolios** who want a structured lens
- **Security teams doing supply chain triage** who want a one-page summary
- **Engineering leaders comparing internal repos** (later, with private-repo support)
- **Students learning what "good code" looks like** by browsing high-scoring repos

## The five principles

These are non-negotiable. Every product decision is checked against them.

### 1. Open formula
The complete scoring formula is published as a Markdown spec, versioned (v1.0, v1.1, ...). Every weight, every threshold, every penalty is documented. Old scores stay valid against the version they were computed under. Anyone can fork the formula, run it themselves, and challenge ours.

### 2. Free for public repositories — forever
There will never be a "Pro tier" that gates public-repo scoring. If we monetize later, it will be on private-repo scanning, organization dashboards, or API quotas — never on the public benchmark that gives the project its credibility.

### 3. Shareable by default
Every scan produces a permalink. Every permalink has an embed badge SVG. Reports are public. The act of scanning a repo is a public contribution to the benchmark.

### 4. Peer-reviewable
Comments, discussion, and dispute on every report. If a maintainer disagrees with a Semgrep finding, they can mark it false-positive with a reason and that note shows on the report. The community can upvote good critiques.

### 5. Reproducible
Scan a repo today, scan it again tomorrow with no code changes, and the score should not move. Every scan stores the formula version, tool versions, and seed inputs used so reruns are deterministic. We publish the raw outputs so anyone can recompute.

## What StackHealth will explicitly NOT do

Saying no early prevents scope creep:

- **Not a CI replacement.** We don't gate PRs or run on every commit. Scans are user-initiated or weekly.
- **Not a linter.** We aggregate other tools' output, we don't ship our own rule engine.
- **Not a security product.** We surface findings; we don't promise breach prevention.
- **Not a code search engine.** We don't index source code for browsing.
- **Not an AI code review.** We don't generate prose feedback or fix PRs. (Maybe in v3, never in MVP.)

## Success criteria, year one

- 10,000 unique repositories scanned
- 500 badges embedded in public READMEs (the viral loop)
- 1,000 GitHub stars on the StackHealth repo
- 3 conference/blog mentions citing StackHealth as a "standard"
- $0 raised, profitable on a $50/month infra budget

This is built solo, in evenings and weekends, for the love of the problem. It does not need to be a business to be a success.
