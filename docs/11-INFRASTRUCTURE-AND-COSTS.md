# 11 — Infrastructure and Costs

> What the project costs to run, where every dollar goes, and how it scales.

## TL;DR

- **Month 1–3 (MVP + Phase 2):** $15–25/month
- **Months 4–6 (Phase 3, growing):** $30–60/month
- **At 10k scans/day (good problem):** $150–250/month
- **Domain:** $12 one-time/year

This is built to be sustainable from a personal credit card. No fundraising assumed.

---

## Service-by-service breakdown

### Vercel (Frontend hosting)

| Tier | Cost | What you get | When you outgrow it |
|------|------|--------------|---------------------|
| Hobby | $0 | 100 GB bandwidth, unlimited deploys, ISR | When you cross 100 GB/month bandwidth — roughly 50k report views/month |
| Pro | $20/month | 1 TB bandwidth, analytics | At ~500k report views/month |

**MVP cost: $0.** Realistic Phase 2/3 cost: $0–20.

If we hit Vercel commercial-use limits, we move to **Cloudflare Pages** ($0, unlimited bandwidth) for the same workload.

### Fly.io (API + Worker)

Two apps, both running `shared-cpu-1x` machines (256 MB RAM).

| Component | Machine | Cost/month |
|-----------|---------|-----------|
| API | 1× shared-cpu-1x, 256 MB | $1.94 |
| Worker | 1× shared-cpu-1x, 512 MB (needs more for Semgrep) | $3.89 |
| Bandwidth | First 160 GB free | $0 |

**MVP cost: ~$6/month.**

At Phase 3 (running more workers in parallel): 2 workers + 1 API ≈ $10/month.

At 10k scans/day: 5–10 workers ≈ $25–50/month.

### Neon (Postgres)

| Tier | Cost | What you get |
|------|------|--------------|
| Free | $0 | 0.5 GB storage, 1 branch, autopause |
| Launch | $19/month | 10 GB, no autopause, 5 branches, point-in-time restore |
| Scale | $69/month | 50 GB, autoscaling |

**MVP cost: $0.** We hit free-tier limits around 4k scans, then upgrade.

### Upstash (Redis)

| Tier | Cost | What you get |
|------|------|--------------|
| Free | $0 | 10k commands/day, 256 MB |
| Pay-as-you-go | $0.20 per 100k commands | No daily cap |
| Pro | $10/month | 1M commands/day, 1 GB |

**MVP cost: $0.** RQ uses ~5 commands per job; 1k jobs/day = 5k commands, well under free tier.

### Cloudflare R2 (Object storage)

- $0.015/GB/month storage
- $0 egress (the killer feature)
- Free tier: 10 GB storage, 1M Class A ops/month, 10M Class B ops/month

Raw scan outputs average ~200 KB per scan. 10,000 scans = 2 GB. **MVP cost: $0.** At 100k scans: 20 GB = $0.30/month.

### Cloudflare (DNS + CDN + Turnstile)

- DNS + proxy: $0
- Turnstile CAPTCHA: $0

### Domain (Namecheap / Porkbun)

`stackhealth.dev`: ~$12/year.

### Sentry (Error tracking)

| Tier | Cost | Errors/month |
|------|------|--------------|
| Developer | $0 | 5k errors |
| Team | $26/month | 50k errors |

**MVP cost: $0** unless we get popular fast.

### Plausible (Analytics)

| Tier | Cost | Pageviews/month |
|------|------|-----------------|
| Growth | $9/month | 10k |
| Business | $19/month | 100k |

Privacy-respecting, no cookie banner needed. Self-hostable later if cost matters.

**MVP cost: $9/month** (Growth tier).

### GitHub (Code + Actions)

- Public repos: $0
- Actions: 2000 free minutes/month for personal accounts (way more than we'll use)

### Better Stack (Status page) — optional

| Tier | Cost |
|------|------|
| Free | $0 (1 monitor, basic) |
| Starter | $19/month |

**MVP: $0.** A public status page builds credibility cheaply.

---

## Cost tables

### Month 1 (MVP launch month)

| Item | Cost |
|------|------|
| Vercel Hobby | $0 |
| Fly.io (API + Worker, light usage) | $6 |
| Neon Free | $0 |
| Upstash Free | $0 |
| Cloudflare R2 | $0 |
| Cloudflare DNS + Turnstile | $0 |
| Sentry Free | $0 |
| Plausible Growth | $9 |
| Better Stack Free | $0 |
| Domain (amortized) | $1 |
| **Total** | **~$16/month** |

### Month 6 (Phase 3, 5k scans/month)

| Item | Cost |
|------|------|
| Vercel Hobby (still free) | $0 |
| Fly.io (3 workers + API) | $14 |
| Neon Launch (upgraded) | $19 |
| Upstash Free (still fits) | $0 |
| Cloudflare R2 (5 GB) | $0 (within free tier) |
| Sentry Free | $0 |
| Plausible Growth | $9 |
| Domain | $1 |
| **Total** | **~$43/month** |

### Scale scenario (10k scans/day, viral moment)

| Item | Cost |
|------|------|
| Vercel Pro | $20 |
| Fly.io (10 workers + 2 API) | $60 |
| Neon Scale | $69 |
| Upstash Pro | $10 |
| Cloudflare R2 (50 GB) | $1 |
| Sentry Team | $26 |
| Plausible Business | $19 |
| Domain | $1 |
| **Total** | **~$206/month** |

At this scale, the paid tier (Phase 4) easily covers infra.

---

## Hard caps to avoid surprise bills

Configure these on Day 1:

| Service | Cap |
|---------|-----|
| Fly.io | Set `min_machines_running = 1`, `max_machines_running = 5` per app |
| Vercel | Use Hobby tier (auto-caps); set bandwidth alerts |
| Upstash | Free tier hard-caps automatically |
| Neon | Auto-suspend after 5 min idle (free tier default) |
| R2 | Cloudflare dashboard: set spend alert at $10/month |

Set up budget alerts in your email for $25, $50, $100/month thresholds.

---

## CI/CD

GitHub Actions, single workflow on each repo:

| Repo | Workflow |
|------|---------|
| `stackhealth` (app) | On push to `main`: lint → test → build → `fly deploy api` + `fly deploy worker` + Vercel auto-deploys via GitHub integration |
| `formula` (spec) | On push: validate markdown, check version bump is correct, regenerate `formula.json` from markdown |
| `docs` (this folder) | On push: deploy to docs.stackhealth.dev (Mintlify free tier or just GitBook) |

Branch protection: PR + 1 approval (eventually), passing CI, no force-push.

---

## Backup strategy

- **Database:** Neon's free tier includes daily snapshots, 7-day retention. Sufficient.
- **Object storage:** R2 is replicated by Cloudflare. We don't need our own backups.
- **Code:** GitHub is the source of truth. Local clones on your machine.
- **Secrets:** Stored in `1Password` (personal vault). Never committed.

---

## Monitoring

| What | How | Where |
|------|-----|-------|
| Uptime | Better Stack monitors `stackhealth.dev` and `api.stackhealth.dev/health` every 60s | Email + push notification on down |
| Errors | Sentry on both API and worker | Email + Sentry alerts |
| Worker queue depth | Fly.io metrics + custom Sentry breadcrumb | Slack/email if queue > 100 |
| Performance | Vercel Analytics + Plausible | Weekly review |
| Spend | Fly.io + Vercel email alerts | Monthly review |

---

## Disaster recovery

| Scenario | What to do | Time to recover |
|----------|-----------|------------------|
| Worker crashes | Auto-restart via Fly | < 60s |
| Postgres down | Neon paid tier failover; free tier ~5 min | 5 min |
| Vercel down | Cloudflare Pages fallback (DNS swap) | 30 min |
| R2 down | Reads fail temporarily; new scans queue | <1 hour (CF SLA) |
| Domain hijacked | Out of scope — use 2FA on registrar |
| Entire service down | Static `/status` page on Cloudflare Pages explaining outage | 5 min to publish |

---

## When to add a paid tier

Three signals say it's time:

1. Infra costs exceed $50/month consistently
2. >5 different people email asking for private-repo scanning
3. >100 GitHub Action installs

Pricing already designed in `06-ROADMAP.md`. Implementation effort: ~2 weeks.
