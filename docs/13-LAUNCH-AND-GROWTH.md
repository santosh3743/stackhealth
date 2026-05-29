# 13 — Launch and Growth

> A go-to-market plan for a solo, bootstrapped, evenings-and-weekends project. The goal is not "growth at all costs" — it's earning enough trust that StackHealth becomes a thing developers cite.

## The differentiated story

StackHealth's positioning in three sentences:

> CodeFactor and SonarCloud are great tools, but their formulas are closed and gated behind paid tiers. OpenSSF Scorecard tells you about security but ignores code quality. StackHealth is the first composite code-health score with a fully open formula — free for every public repo, forever, with raw outputs you can verify.

Lead with **open**, **free**, **transparent**. These are credibility multipliers, not gimmicks.

---

## Pre-launch (Weeks 1–4, while building)

### Build in public

- Tweet/post on LinkedIn weekly: "Week 1 building StackHealth — here's what's done, here's what's stuck."
- Use the same screenshots in a dev.to series
- Tag relevant communities (#100DaysOfCode, #buildinpublic)
- Reply to people who reply

You're not chasing followers — you're building an audience that cares about the launch.

### Get early-access feedback

- DM 20 OSS maintainers (Python, JS, Rust, Go) with a personalized note: "I'm building an open code-health benchmark. Would you be open to seeing how your repo scores before public launch? 5-min feedback request."
- Their feedback shapes Week 4 polish
- Their permission to feature their report on launch day = social proof

### Pre-warm the URLs

- Pre-scan 50 well-known repos in Week 4. Their report URLs exist at launch.
- Bonus: many of those maintainers will tweet about their score when they discover it.

---

## Launch day (end of Week 4)

The four channels, in order of priority:

### 1. Hacker News (Show HN)

- Post at **8:00 AM Pacific** on a **Tuesday or Wednesday** (highest engagement window)
- Title format: `Show HN: StackHealth – open-formula code health score for any GitHub repo`
- Description: 2 short paragraphs. What it is, why it's different (open formula).
- First comment from you: "Author here. Happy to answer questions. The formula is documented at stackhealth.dev/methodology and lives in github.com/santosh3743/stackhealth/tree/main/packages/formula-spec. Roast away."
- Stay on HN for 12 hours straight responding to every comment.

### 2. Product Hunt

- Schedule for the next day after HN (so HN buzz can boost PH)
- Tagline: "The open code health benchmark"
- 5 gallery images: landing page, sample report, methodology snippet, badge embed example, leaderboard mock
- First comment from you with the same vibe as HN
- Ask 20 friends/colleagues to upvote — do NOT mass-DM, just personal asks

### 3. Reddit

- r/programming: Same Show HN-style post, more technical framing
- r/opensource: Lean into the "open formula" angle
- r/javascript, r/python, r/golang, r/rust: One post each, language-specific report examples

### 4. X / Twitter / LinkedIn thread

- 8–10 tweet thread, screenshot-heavy, ending with the launch link
- Cross-post the same content as a LinkedIn longpost
- Tag a few well-known dev influencers (don't @-spam — only if genuinely relevant)

---

## Week 5–12 — Growth tactics

### Viral loops baked into the product

Every product mechanic is a distribution mechanic:

1. **Badge embeds** — Each badge SVG includes `referrer` analytics. The more README badges, the more inbound traffic.
2. **Permalinks** — Sharing a report is one click. URLs are pretty (`stackhealth.dev/r/fastapi/fastapi`).
3. **OG images** — Every report has a 1200×630 social-preview image. Shared = beautiful on Twitter/LinkedIn.
4. **Sub-score callouts** — "fastapi/fastapi scored A+ on Hygiene 🥇" — auto-generated tweet templates from the share button.

### Targeted maintainer outreach

A weekly batch of 10 emails to maintainers of popular OSS projects:

> Hi [name], I scanned [repo] on StackHealth — it scored B+ overall. The detail is here: [link]. The formula is fully open at [link] in case you want to see how we got there. If anything looks wrong or you'd want to mark a false positive, your verified-maintainer login is one click via GitHub OAuth. Cheers, [you].

Don't pitch. Just share the data. The conversation starts itself.

### Cite-worthy content

Write quarterly blog posts that the community would link to:

- "The State of Code Health: Q3 2026" — aggregate stats across 10k repos
- "What separates A+ repos from B repos" — pattern analysis
- "Why we changed the formula from v1.0 to v1.1" — transparency in action
- "We scanned every Python package on PyPI" — buzzy, link-bait, but earned

Each post becomes a backlink magnet and a credibility artifact.

### Conference / talk circuit (Month 6+)

Pitch lightning talks at:
- PyCon, EuroPython
- GopherCon
- FOSDEM (Open Source dev room)
- Local meetups (cheap, fast practice)

Topic: "Designing a transparent benchmark — the StackHealth formula." Talk content is the methodology doc, presented well.

### Partnerships (Month 6+)

Quiet outreach to:
- **Astral (ruff, uv)** — share Python-ecosystem stats with them
- **Sourcegraph** — possible badge integration
- **OpenSSF** — co-promotion of the security score
- **Read the Docs** — auto-show StackHealth badge in their docs pages

Don't ask for money or co-marketing — just share data, get on their radar.

---

## What success looks like

| Metric | 30 days | 90 days | 1 year |
|--------|---------|---------|--------|
| Total scans | 500 | 5,000 | 50,000 |
| Unique repos scanned | 300 | 3,000 | 20,000 |
| Embedded badges (measured via referrer) | 10 | 200 | 2,000 |
| GitHub stars (app repo) | 100 | 500 | 3,000 |
| GitHub stars (formula repo) | 50 | 300 | 1,500 |
| Formula community PRs | 0 | 5 | 50 |
| Press / blog mentions | 1 | 5 | 30 |
| Conf talk acceptances | 0 | 0 | 2 |

If we miss these by 30%, that's still a healthy project. If we miss by 80%, re-evaluate at the 6-month mark.

---

## What to ignore

These are tempting and wasteful for a solo bootstrapper:

- **SEO content farms** — Writing 50 thin blog posts doesn't help. Write 5 great ones a year.
- **Paid ads** — Inappropriate for a freemium dev tool. ROI is negative until enterprise tier.
- **Conference booths** — $5k+ for a folding table. Skip until you have a customer base.
- **Influencer payments** — Ineffective in dev space and hurts credibility.
- **Email newsletters** — Don't start one until you have a clear weekly value to share.
- **A Discord server** — Don't start one until 1,000+ active users. Empty Discord is worse than no Discord.
- **A YouTube channel** — Production cost > audience value, for now.

---

## Failure scenarios — when to pivot or stop

After 6 months, if you have <50 daily scans, <30 embedded badges, and no inbound press, the product hasn't landed. Don't double down — try one of:

- **Pivot to internal tool:** Package StackHealth as a self-hosted product for engineering teams. Different GTM (B2B sales) but proven need.
- **Pivot to GitHub-App-only:** Skip the public benchmark idea, focus on PR scoring as a CI step. Bigger field but more competition.
- **Wind down gracefully:** Open-source everything, keep the formula repo maintained, sunset the hosted service. The formula itself can still be a contribution.

The worst outcome isn't failure — it's spending 2 years on something that's not working without seeing the signal. Set the 6-month checkpoint now.

---

## The non-financial measure of success

Even if no metric above is hit, ask at the 6-month mark:

> Did I learn enough — about formula design, about static analysis, about running production infra solo, about marketing a dev tool — that I'd take this on again?

If yes, the project paid for itself in education. Most side projects fail at metrics. Few pay back in skills. Aim for both, take either.
