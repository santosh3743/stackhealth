# Security policy

Thank you for taking the time to look. StackHealth is a developer tool
that fetches public repositories and runs static analyzers against them,
so the surface that matters most is:

- The HTTP API and its rate limits
- The worker sandbox (which clones and analyzes untrusted repos)
- The persistence layer (Postgres + Redis)
- The way we render scan output back to users

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Use one of the following private channels instead:

1. **Preferred** — GitHub's private vulnerability reporting:
   open this repository's [Security tab](https://github.com/santosh3743/stackhealth/security)
   → **Report a vulnerability**.
2. **Email** — `santosh3743@gmail.com` with a clear subject line
   beginning with `[security]`.

Include enough information for the maintainer to reproduce. A minimal
report contains:

- A description of the issue and its impact
- A reproduction (URL, request payload, scan ID, repo URL, etc.)
- Affected version or commit SHA
- Any suggested mitigation

## What to expect

| Step | Target time |
|---|---|
| Initial acknowledgement | within 3 business days |
| Assessment of severity and validity | within 7 business days |
| Patch released (low/medium severity) | within 30 days |
| Patch released (high/critical) | as fast as humanly possible |

We will keep you in the loop as the fix progresses, credit you in the
release notes if you'd like, and coordinate the public disclosure date
with you.

## Scope

These are in scope:

- The hosted API at `api.stackhealth.dev`
- The web app at `stackhealth.dev`
- The worker's repo clone + scan pipeline (`apps/api/stackhealth/worker/`)
- The scoring engines under `apps/api/stackhealth/engines/`
- Anything in this repository that runs server-side
- Outbound integrations (Resend, GitHub API, OpenSSF Scorecard API,
  Cloudflare R2) — particularly where we might leak credentials or
  user data

These are out of scope:

- Vulnerabilities in third-party dependencies that have already been
  publicly disclosed and are tracked by Dependabot — please open a
  normal issue if you think we're missing an update
- Rate-limiting or volumetric DoS that don't bypass authentication or
  reveal data
- Social engineering of the maintainer
- Issues that require physical access to a contributor's machine
- Self-XSS or "user clicks a malicious URL with a payload they wrote"
- The scanning sandbox executing third-party static analyzers — these
  are documented dependencies; vulns there should be reported upstream
  first

## Disclosure

Once a fix is released we will:

1. Publish a GitHub Security Advisory.
2. Note the fix in `CHANGELOG.md` (with a CVE if one was assigned).
3. Credit the reporter (with permission).

We do not currently run a paid bug-bounty program. We will publicly
thank you and, if you'd like, link to your website or profile in the
advisory.

## A note on the worker sandbox

The worker clones arbitrary public GitHub repositories and runs static
analyzers against them. That's a deliberately tightly-bounded surface
(no install steps, no test execution, no `make`, hard timeouts, size
caps), but if you find a way to make any of the engines execute
arbitrary code on the worker — for example through a malicious
`.semgrep.yml`, a crafted dependency manifest, or a Trivy plugin — we
consider that high severity and want to hear about it immediately.

See [`docs/12-SECURITY-AND-PRIVACY.md`](./docs/12-SECURITY-AND-PRIVACY.md)
for the sandbox design details.
