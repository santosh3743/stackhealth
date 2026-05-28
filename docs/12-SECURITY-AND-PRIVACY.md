# 12 — Security and Privacy

> StackHealth scans other people's code. That creates trust obligations from day one. This document lists every thing we store, every thing we don't, and how the scanning sandbox is contained.

## The two-line promise we make to users

1. **We only scan public repositories. We never store source code beyond the scan job.**
2. **Every output we produce is public.** No private data exists in our system because no private inputs ever enter.

---

## Data inventory — what we store

| Data | Where | Retention | Why |
|------|-------|-----------|-----|
| Repo metadata (owner, name, stars, language, license) | Postgres `repos` | Indefinite | Required for reports |
| Scan record (status, scores, commit SHA, tool versions) | Postgres `scans` | Indefinite | The report itself |
| Findings (rule, severity, file, line, snippet) | Postgres `scan_findings` | Indefinite | Report display |
| Raw engine outputs (JSON from Semgrep, Trivy, Scorecard, cloc) | Cloudflare R2 | Indefinite | Transparency / reproducibility |
| Requester IP (for rate limiting) | Postgres `scans.requested_by_ip` | 30 days, then nulled | Rate limit + abuse |
| Server access logs | Fly.io / Vercel | 7 days (default) | Debugging |
| Analytics events (page views) | Plausible | Per Plausible policy (no PII) | Product analytics |

## Data inventory — what we DO NOT store

| Data | Why we don't store it |
|------|----------------------|
| **Source code itself** | Cloned to ephemeral tmpdir in worker, deleted immediately after scan |
| **Git history beyond HEAD** | Shallow clone (`--depth 1`) — we never have history |
| **Private repo content** | We refuse to scan private repos in MVP. Phase 4 GitHub App will require explicit org install. |
| **User accounts** | None in MVP. Phase 2 adds OAuth, but we store only `github_id`, `login`, `avatar_url`. No email unless user opts in. |
| **Credit card info** | We don't process payments in MVP. Phase 4 uses Stripe; we never see the card. |
| **Cookies for tracking** | Plausible is cookie-less. We use one `session` cookie only post-login (Phase 2). |

---

## Scanning sandbox — how a scan can't hurt us

The worker is the most security-sensitive part of StackHealth. We're executing untrusted code-adjacent operations (cloning arbitrary repos, running parsers over them) on our infrastructure.

### Container isolation

- The worker runs in a Fly.io VM (Firecracker microVM). Hardware isolation between workers.
- Each scan runs in its own subprocess; if Semgrep crashes, only that subprocess dies.

### No code execution

**We never execute repo code.** We only:
- Read files from the cloned repo
- Parse them with static analyzers (Semgrep, Trivy, cloc, ruff, eslint with `--no-eslintrc`)

We do NOT:
- Run `pip install`, `npm install`, or any package manager
- Execute `make`, `setup.py`, or build scripts
- Run tests
- Evaluate any code in the repo

This means we miss some signals (e.g., a JS project's actual dependency tree requires `npm install` to fully resolve). We accept this trade-off — the security gain is worth it.

### Resource limits per scan

- **Disk:** Clone capped at 500 MB (`git clone --filter=blob:limit=500m`)
- **CPU time:** 5 minutes wall-clock max per scan (`timeout 300`)
- **Memory:** 512 MB worker process; Semgrep capped at 256 MB
- **Network during scan:** Worker has outbound only; clone over HTTPS only, no shell access to it

Beyond these limits, the scan is killed and marked `failed` with reason `resource_limit`.

### Path traversal & symlink defense

- Clone into a per-scan tmpdir like `/tmp/scan-{uuid}/repo/`
- All engine invocations use absolute paths into that tmpdir
- Reject any output path outside the tmpdir
- Refuse to follow symlinks pointing outside the clone

### Cleanup guarantee

Every scan job uses Python's `with tempfile.TemporaryDirectory()`:

```python
def run_scan(scan_id: UUID):
    with tempfile.TemporaryDirectory(prefix=f"scan-{scan_id}-") as workdir:
        ...
    # tmpdir is guaranteed deleted on exit, success or failure
```

A periodic janitor sweeps `/tmp/scan-*` directories older than 1 hour, in case anything escapes.

---

## Authentication & authorization (Phase 2+)

When we add GitHub OAuth:

- OAuth scopes requested: `read:user`, `user:email` (only if user opts in)
- **No write scopes.** We never get permission to write to a user's repos.
- Tokens stored encrypted at rest in Postgres (`pgcrypto`)
- Tokens never logged or sent to error trackers
- Sessions use `httponly`, `secure`, `samesite=lax` cookies

Repo claiming verification (Phase 2):
- User signs in with GitHub
- We check via GitHub API whether they have `push` access to the repo they're claiming
- If yes, they get a "verified maintainer" badge on the report and can mark findings as false positive

---

## API security

- All endpoints HTTPS only (HSTS preload)
- CORS: only `stackhealth.dev` and `*.vercel.app` previews
- Rate limiting per IP (and per user in Phase 2)
- Input validation via Pydantic
- SQL injection: prevented by SQLAlchemy parameterized queries
- XSS in reports: all user-supplied text (findings messages, file paths) escaped on render
- CSRF: enforced via `samesite=lax` cookies + double-submit token on auth'd endpoints

---

## Secrets management

- Production secrets in Fly.io's encrypted secret store (`fly secrets set`)
- GitHub PAT for API access: read-only token, scope `public_repo` only
- Database connection strings, Redis URL, R2 keys all in Fly secrets
- Local dev: `.env.local` gitignored, sample in `.env.example`
- 1Password personal vault as backup
- Secrets rotated annually or on team change

---

## Vulnerability response

- Public security policy at `SECURITY.md` in the main repo
- Disclosure email: `security@stackhealth.dev`
- Target response time: 48 hours
- We commit to:
  - Acknowledge receipt within 48h
  - Patch critical issues within 7 days
  - Public disclosure 30 days after patch (or sooner if exploited)
- We use OpenSSF Scorecard on our own repos. Eat our own dog food.

---

## Privacy policy summary (for the `/privacy` page)

Plain-English version (legal page will be longer):

> StackHealth only scans public GitHub repositories. We don't keep your source code — we clone it temporarily, run open-source analyzers, then delete it. The scores and findings we publish are derived from public information about your code. We collect anonymous analytics on which pages people view, using Plausible (cookie-less). When you sign in with GitHub (optional), we store your GitHub username, ID, and avatar — nothing else unless you tell us your email. We don't sell data. We don't track you across sites. You can email `privacy@stackhealth.dev` to delete any data we have about you.

---

## Compliance (eventually)

For MVP, we don't need formal compliance — no PII processed at scale, no payments yet.

Phase 4 (paid tier, org dashboards):
- Stripe handles all PCI scope
- GDPR-style data export + deletion endpoint at `/api/v1/users/me/data` and DELETE method
- Cookie banner if we ever add tracking cookies (currently planned: never)
- SOC 2 considered only if enterprise customers request it (~$30k/year overhead — only worth it with a real customer)

---

## Bug bounty

Once we have ~500 users, we'll launch a small bug bounty program on GitHub Security Advisories ($50–500 range). Until then, security disclosures get a public thanks in our README + a t-shirt.
