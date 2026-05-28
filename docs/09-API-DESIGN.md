# 09 — API Design

> FastAPI endpoints for the MVP and Phase 2. RESTful, JSON, OpenAPI auto-generated at `/api/docs`.

Base URL: `https://api.stackhealth.dev`

All responses are JSON. All times are ISO 8601 UTC. All IDs are UUID v4.

---

## Authentication

**MVP:** None. Anonymous. Rate-limited by IP.

**Phase 2:** Optional GitHub OAuth. Authenticated requests get higher rate limits.

**Phase 3:** API keys for programmatic use (header: `Authorization: Bearer sh_live_<key>`).

---

## Rate limits

| Endpoint group | Anonymous | Authenticated (Phase 2+) |
|----------------|-----------|--------------------------|
| `POST /api/scans` | 5/IP/hour | 30/user/hour |
| `GET /api/scans/:id` | 60/IP/min (just polling) | 120/user/min |
| `GET /api/repos/...` | 30/IP/min | 60/user/min |
| `GET /api/leaderboard` | 10/IP/min | 30/user/min |
| `GET /badge.svg` | unlimited (cached) | unlimited |

Headers on every response:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1716998400
```

---

## Scans

### `POST /api/scans`

Submit a new scan.

**Request:**
```json
{
  "repo_url": "https://github.com/fastapi/fastapi"
}
```

**Response 202 Accepted:**
```json
{
  "scan_id": "9f8b3a2c-...",
  "status": "queued",
  "polling_url": "/api/scans/9f8b3a2c-...",
  "report_url": "/r/fastapi/fastapi/9f8b3a2c-..."
}
```

**Errors:**
- `400` — Invalid URL (not github.com, malformed)
- `404` — Repo does not exist or is private
- `409` — A scan for this repo was already created in the last hour (returns existing `scan_id`)
- `429` — Rate limit exceeded
- `503` — Worker queue full (rare)

### `GET /api/scans/:scan_id`

Read current scan status and result (if complete).

**Response 200 (in progress):**
```json
{
  "id": "9f8b3a2c-...",
  "repo": { "owner": "fastapi", "name": "fastapi" },
  "status": "analyzing",
  "engines_complete": ["scorecard", "hygiene"],
  "engines_pending": ["semgrep", "trivy", "lint"],
  "formula_version": "v1.0",
  "created_at": "2026-05-28T10:15:00Z"
}
```

**Response 200 (complete):**
```json
{
  "id": "9f8b3a2c-...",
  "repo": { "owner": "fastapi", "name": "fastapi", "stars": 78000, "language": "Python" },
  "status": "complete",
  "formula_version": "v1.0",
  "commit_sha": "abc123...",
  "overall_score": 89,
  "grade": "A-",
  "scores": {
    "security": 86,
    "quality": 84,
    "hygiene": 97,
    "community": 92
  },
  "score_breakdown": {
    "scorecard": 85,
    "semgrep": 91,
    "dependencies": 78,
    "complexity": 80,
    "lint_density": 88,
    "duplication": 90,
    "test_signal": 85,
    "file_size": 75
  },
  "partial": false,
  "artifacts_url": "https://artifacts.stackhealth.dev/scans/9f8b3a2c.../",
  "tool_versions": {
    "semgrep": "1.50.0",
    "trivy": "0.48.0",
    "scorecard": "5.0.0",
    "cloc": "1.98"
  },
  "created_at": "2026-05-28T10:15:00Z",
  "completed_at": "2026-05-28T10:16:22Z"
}
```

### `GET /api/scans/:scan_id/findings`

Paginated findings list.

**Query params:**
- `engine` — filter (semgrep, trivy, lint, …)
- `severity` — filter (critical, high, medium, low, info)
- `cursor` — pagination cursor
- `limit` — default 50, max 200

**Response 200:**
```json
{
  "findings": [
    {
      "id": "f1...",
      "engine": "semgrep",
      "severity": "high",
      "rule_id": "python.lang.security.audit.dangerous-eval",
      "title": "Detected dangerous use of `eval`",
      "message": "Use ast.literal_eval instead.",
      "file_path": "src/utils/parse.py",
      "line_number": 42,
      "code_snippet": "result = eval(user_input)"
    }
  ],
  "next_cursor": "eyJpZCI6...",
  "total": 87
}
```

---

## Repos

### `GET /api/repos/:owner/:name`

Get info about a repo + its scan history.

**Response 200:**
```json
{
  "owner": "fastapi",
  "name": "fastapi",
  "stars": 78000,
  "language": "Python",
  "license_spdx": "MIT",
  "latest_scan": { "id": "...", "grade": "A-", "overall_score": 89, "completed_at": "..." },
  "scan_history": [
    { "id": "...", "grade": "A-", "overall_score": 89, "completed_at": "2026-05-28T..." },
    { "id": "...", "grade": "B+", "overall_score": 84, "completed_at": "2026-04-15T..." }
  ],
  "first_seen_at": "2025-12-01T..."
}
```

### `GET /api/repos/:owner/:name/latest`

Shortcut to the latest complete scan.

Same shape as `GET /api/scans/:scan_id` for that scan.

---

## Badge

### `GET /r/:owner/:name/badge.svg`

Serves an SVG badge with the latest scan's grade and score.

**Query params:**
- `style` — `flat` (default), `for-the-badge`, `social`
- `label` — custom label (default: "stackhealth")

**Response 200 (image/svg+xml):**
A small SVG, ~600 bytes. Cache headers: `Cache-Control: public, max-age=3600, s-maxage=3600`.

If the repo has no scan yet, badge shows "no scan".

---

## Discover / Leaderboard (Phase 2)

### `GET /api/discover`

Recent + trending scans.

**Query params:**
- `tab` — `recent` (default) or `trending` (most-viewed in 7d)
- `limit` — default 20, max 100

**Response 200:**
```json
{
  "scans": [
    {
      "id": "...", "owner": "user", "name": "repo",
      "grade": "B+", "overall_score": 84, "stars": 1234,
      "language": "Rust", "completed_at": "..."
    }
  ]
}
```

### `GET /api/leaderboard`

Top repos by score within a language.

**Query params:**
- `language` — required (case-insensitive): `python`, `javascript`, `typescript`, `go`, `rust`, `java`, …
- `min_stars` — default 100, prevents gaming
- `limit` — default 50

**Response 200:** Same shape as `/api/discover`.

---

## Formula (Phase 2)

### `GET /api/formula/versions`

List all published formula versions.

```json
{
  "versions": [
    { "version": "v1.0", "published_at": "...", "spec_url": "...", "summary": "..." }
  ]
}
```

### `GET /api/formula/:version`

Returns the machine-readable formula spec for a version (weights, thresholds).

---

## Health / status

### `GET /api/health`

```json
{ "status": "ok", "version": "0.4.2", "formula_version": "v1.0" }
```

### `GET /api/stats`

Public live statistics for the landing page.

```json
{
  "total_repos_scanned": 12483,
  "total_scans": 19872,
  "scans_last_24h": 412,
  "median_overall_score": 67,
  "median_scan_duration_seconds": 78
}
```

---

## Webhooks (Phase 4)

`POST /api/v1/webhooks` — register a webhook URL for a repo. Fires on each new scan completion.

Payload signing via HMAC-SHA256 in `X-StackHealth-Signature` header.

---

## Errors

Standard error envelope:

```json
{
  "error": {
    "code": "rate_limited",
    "message": "Rate limit exceeded. Try again in 600 seconds.",
    "request_id": "req_..."
  }
}
```

Error codes:
- `invalid_url`, `repo_not_found`, `repo_private`, `repo_too_large`
- `rate_limited`, `worker_unavailable`
- `internal_error` (with request_id for support)

---

## OpenAPI

FastAPI auto-generates the OpenAPI spec at `https://api.stackhealth.dev/openapi.json`, browsable at `https://api.stackhealth.dev/docs`.
