# StackHealth GitHub Action

Posts a sticky PR comment with the [StackHealth](https://stackhealth.dev) grade of both the base branch and the PR head, plus the delta — so every code review surfaces whether the change is improving or regressing the repo's health.

```
StackHealth grade

|         | Base `main` | This PR `feat/auth` | Δ      |
|---------|-------------|---------------------|--------|
| Overall | **B+** 84   | **A-** 88           | ✅ +4  |
| Security| 80          | 88                  | +8     |
| Quality | 90          | 90                  | ·      |
| Hygiene | 100         | 100                 | ·      |
| Community | 70        | 75                  | +5     |
```

## Usage

```yaml
# .github/workflows/stackhealth.yml
name: StackHealth
on:
  pull_request:
    types: [opened, reopened, synchronize]

permissions:
  contents: read
  pull-requests: write

jobs:
  health:
    runs-on: ubuntu-latest
    steps:
      - uses: santosh3743/stackhealth@v0
        with:
          email: ${{ secrets.STACKHEALTH_EMAIL }}
          min-grade: B   # optional — fail the check if PR grade drops below B
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `email` | yes | — | Email for the scan-complete notifications. The API requires one. Put it in repo secrets. |
| `min-grade` | no | `""` | If set (e.g. `B`, `A-`), the check fails when the PR grade is below this threshold. Leave empty to never fail. |
| `github-token` | no | `${{ github.token }}` | Used to post the PR comment. The default works for same-repo PRs. |
| `api-base` | no | `https://api.stackhealth.dev` | Override for self-hosted / staging. |
| `site-base` | no | `https://stackhealth.dev` | Override the report URL in the comment. |
| `ci-token` | no | `""` | Shared secret sent as the `x-stackhealth-ci` header so a Cloudflare WAF rule can let CI traffic past bot protection. Omit to disable. |

## Outputs

| Output | Example |
|---|---|
| `base-grade` | `B+` |
| `head-grade` | `A-` |
| `base-score` | `84` |
| `head-score` | `88` |
| `delta` | `4` (negative if regressed) |

## Permissions

Needs `pull-requests: write` to post / update the sticky comment. `contents: read` is the GitHub default.

## How it works

1. Reads `pull_request.base.ref` and `pull_request.head.ref` from the workflow context.
2. Submits two scans to the StackHealth API in parallel — one for the base, one for the head.
3. Polls until both complete (or the 10-minute timeout fires).
4. Finds an existing comment with the marker `<!-- stackhealth-action -->` and edits it; otherwise creates a new one.

Each scan respects the public API's rate limits (5 scans / IP / hour) but the per-repo 1-hour dedupe means re-runs on quick succession will reuse the most recent scan — no extra worker time.

## Limits & caveats

- **PRs from forks**: when the source is on a fork, the action scans the fork's branch URL (`pr.head.repo.full_name`). That works because StackHealth scans public repos. If the fork is private, the head scan will fail with a clear message.
- **Long scans**: large repos can take 5–9 minutes to score. The action polls up to 10 minutes per side; tune with `STACKHEALTH_TIMEOUT_SECONDS` in a future release.
- **Branches and tags only**: the underlying API accepts ref names (branches/tags), not SHAs. The action passes `pull_request.head.ref`, which works for any normal PR.

## License

MIT © Santosh Jha
