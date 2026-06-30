# stackhealth

Score any public GitHub repo against the [StackHealth](https://stackhealth.dev) open-formula benchmark — from your terminal.

```bash
$ npx stackhealth fastapi/fastapi
```

```
  fastapi/fastapi
  A   91/100

    Security   ████████████████████  100/100
    Quality    █████████████████···   85/100
    Hygiene    ████████████████████  100/100
    Community  ████████████████····   80/100

  Report:   https://stackhealth.dev/r/fastapi/fastapi/<scan-id>
  Commit:   a1b2c3d
  Formula:  v1.0
```

## Install

You don't need to. `npx stackhealth <repo>` always pulls the latest release.

If you want it on your `$PATH`:

```bash
npm i -g stackhealth
```

### Docker (no Node required)

For CI runners or any environment without Node, run the published image — args
after the image name pass straight through to the CLI:

```bash
docker run --rm ghcr.io/santosh3743/stackhealth-cli pallets/click --json
docker run --rm ghcr.io/santosh3743/stackhealth-cli my-org/my-repo --min-grade B   # exit 1 if below B
```

The image is multi-arch (amd64 + arm64). `:latest` tracks `main`; released
versions are tagged `:X.Y.Z`. To build it yourself instead:

```bash
docker build -f infra/Dockerfile.cli -t stackhealth-cli .   # from the repo root
```

Drop it into any pipeline (GitLab CI, Jenkins, CircleCI, …) the same way you'd
run any other container step.

## Usage

```bash
stackhealth <owner/repo> [options]
```

| Flag | What it does |
|------|-------------|
| `--email <addr>` | Email for the scan-complete notification. Required by the API on first scan. Set `$STACKHEALTH_EMAIL` to skip the flag every time. |
| `--json` | Print the full scan as JSON. No colors, no spinner. Pipe to `jq`. |
| `--min-grade <G>` | Exit non-zero if grade is below `G` (e.g. `B`, `A-`). Use this in CI. |
| `--ref <branch\|tag>` | Score a specific branch or tag instead of the repo's default branch. |
| `--no-wait` | Submit and exit immediately with the scan_id and report URL. Useful when a downstream job will poll, or you just want to trigger a fresh scan. |
| `--badge` | Print the README badge markdown for the repo and exit. No scan is submitted — the badge always reflects the latest grade. |
| `--api <url>` | Override the API base URL. |
| `--site <url>` | Override the report URL base. |
| `--timeout <secs>` | Give up polling after N seconds (default 600). |

The repo argument accepts any of:

- `owner/repo`
- `https://github.com/owner/repo`
- `https://stackhealth.dev/owner/repo`

## Getting a badge for your README

```bash
$ npx stackhealth fastapi/fastapi --badge
[![StackHealth](https://api.stackhealth.dev/r/fastapi/fastapi/badge.svg)](https://stackhealth.dev/r/fastapi/fastapi)
```

Paste that line into your README. The badge SVG always renders the latest grade — no need to re-embed after every scan.

## CI usage

The CLI exits `0` if the scan completes and the grade meets `--min-grade`. Use it as a gate:

```yaml
# .github/workflows/health.yml
- run: npx stackhealth ${{ github.repository }} --min-grade B
  env:
    STACKHEALTH_EMAIL: ${{ secrets.STACKHEALTH_EMAIL }}
```

For richer per-PR feedback with deltas, use the [StackHealth GitHub Action](https://github.com/marketplace/actions/stackhealth) instead.

## Rate limits

The public API limits anonymous callers to 5 scans / IP / hour. Each repo is also deduped to one fresh scan per hour. The CLI surfaces both limits with a clear message.

## Privacy

Only the email is stored, and only to deliver the one-shot completion notification. The repo is cloned shallowly on our worker (no code is ever executed) and the artifacts are public.

## License

MIT © Santosh Jha
