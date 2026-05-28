# apps/api

FastAPI HTTP service + RQ worker. Same Python package, two processes.

## Run locally

```bash
uv sync
cp .env.example .env.local
# fill in DATABASE_URL, REDIS_URL, GITHUB_TOKEN

# Apply migrations
uv run alembic upgrade head

# API (one terminal)
uv run uvicorn stackhealth.api.main:app --reload --port 8000

# Worker (another terminal)
uv run python -m stackhealth.worker.main
```

## Layout

```
stackhealth/
├── config.py          settings (Pydantic Settings, reads .env)
├── database.py        SQLAlchemy engine + session
├── api/
│   ├── main.py        FastAPI app + middleware
│   ├── deps.py        DB session, rate limit deps
│   └── routes/
│       ├── scans.py   POST /scans, GET /scans/:id
│       ├── repos.py   GET /repos/:owner/:name
│       ├── health.py  GET /health
│       └── badge.py   GET /r/:owner/:name/badge.svg
├── worker/
│   ├── main.py        RQ worker entry
│   └── jobs.py        run_scan(scan_id)
├── engines/
│   ├── clone.py       shallow git clone helper
│   ├── github_meta.py GitHub REST metadata fetcher
│   ├── scorecard.py   OpenSSF Scorecard
│   ├── semgrep.py     Semgrep p/security-audit
│   ├── trivy.py       Trivy dependency CVEs
│   ├── cloc.py        LoC by language
│   ├── lint.py        ruff / eslint / golangci-lint
│   └── hygiene.py     README/LICENSE/CI/... checklist
├── formula/
│   └── v1.py          THE OPEN FORMULA (mirror of docs/03 + packages/formula-spec/v1.0.md)
├── models/
│   ├── repo.py        Repo SQLAlchemy model
│   ├── scan.py        Scan + enums
│   └── finding.py     ScanFinding + enums
├── schemas/           Pydantic v2 request/response shapes
├── storage/
│   └── r2.py          Cloudflare R2 upload
└── ratelimit.py       Redis token bucket
```

Spec: `docs/04-ARCHITECTURE.md`, `docs/08-DATA-MODEL.md`, `docs/09-API-DESIGN.md`.
