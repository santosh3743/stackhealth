# 08 — Data Model

> Postgres schema for the MVP. Designed for clarity and easy iteration. We can denormalize for performance later if we need to.

## ER diagram

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────────────┐
│      repos      │ 1     n │      scans       │ 1     n │   scan_findings      │
├─────────────────┤────────►├──────────────────┤────────►├──────────────────────┤
│ id (uuid)       │         │ id (uuid)        │         │ id (uuid)            │
│ owner           │         │ repo_id (fk)     │         │ scan_id (fk)         │
│ name            │         │ status           │         │ engine               │
│ default_branch  │         │ commit_sha       │         │ severity             │
│ description     │         │ formula_version  │         │ rule_id              │
│ stars           │         │ overall_score    │         │ message              │
│ language        │         │ grade            │         │ file_path            │
│ first_seen_at   │         │ security_score   │         │ line_number          │
│ updated_at      │         │ quality_score    │         │ raw_json (jsonb)     │
└─────────────────┘         │ hygiene_score    │         └──────────────────────┘
                            │ community_score  │
                            │ partial (bool)   │
                            │ failure_reason   │
                            │ artifacts_url    │
                            │ requested_by_ip  │
                            │ created_at       │
                            │ completed_at     │
                            └──────────────────┘

┌────────────────────────┐         ┌──────────────────────┐
│   formula_versions     │         │   rate_limits        │
├────────────────────────┤         ├──────────────────────┤
│ version (pk varchar)   │         │ key (varchar pk)     │
│ published_at           │         │ count (int)          │
│ spec_url               │         │ window_start         │
│ summary                │         └──────────────────────┘
└────────────────────────┘
```

---

## Tables

### `repos`

One row per unique repository ever scanned.

```sql
CREATE TABLE repos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner           TEXT NOT NULL,
    name            TEXT NOT NULL,
    default_branch  TEXT,
    description     TEXT,
    homepage        TEXT,
    language        TEXT,            -- primary language from GitHub
    stars           INTEGER,
    forks           INTEGER,
    license_spdx    TEXT,            -- e.g. 'MIT', 'Apache-2.0'
    is_archived     BOOLEAN DEFAULT FALSE,
    is_fork         BOOLEAN DEFAULT FALSE,
    pushed_at       TIMESTAMPTZ,     -- last push on GitHub
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (owner, name)
);

CREATE INDEX idx_repos_language ON repos(language);
CREATE INDEX idx_repos_stars ON repos(stars DESC);
```

Owner + name is the natural key. We store the GitHub metadata refreshed at scan time.

### `scans`

One row per scan attempt.

```sql
CREATE TYPE scan_status AS ENUM (
    'queued', 'cloning', 'analyzing', 'scoring', 'complete', 'failed'
);

CREATE TYPE letter_grade AS ENUM (
    'A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F'
);

CREATE TABLE scans (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id            UUID NOT NULL REFERENCES repos(id) ON DELETE CASCADE,
    status             scan_status NOT NULL DEFAULT 'queued',
    formula_version    TEXT NOT NULL,        -- e.g. 'v1.0'
    commit_sha         TEXT,                 -- the SHA actually scanned
    -- scores (NULL until complete)
    overall_score      INTEGER,              -- 0-100
    grade              letter_grade,
    security_score     INTEGER,
    quality_score      INTEGER,
    hygiene_score      INTEGER,
    community_score    INTEGER,
    -- sub-engine scores stored as JSON for transparency
    score_breakdown    JSONB,                -- {scorecard: 85, semgrep: 91, ...}
    partial            BOOLEAN DEFAULT FALSE,-- true if some engines failed
    failure_reason     TEXT,                 -- e.g. 'clone_timeout' if status=failed
    artifacts_url      TEXT,                 -- R2 prefix, e.g. https://r2.../scans/{id}/
    tool_versions      JSONB,                -- {semgrep: '1.x', trivy: '0.x', ...}
    requested_by_ip    INET,                 -- for rate limiting (nullable, hashed in v1.1)
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at       TIMESTAMPTZ
);

CREATE INDEX idx_scans_repo_complete ON scans(repo_id, completed_at DESC)
    WHERE status = 'complete';
CREATE INDEX idx_scans_status ON scans(status) WHERE status != 'complete';
CREATE INDEX idx_scans_created ON scans(created_at DESC);
```

`score_breakdown` is a JSONB column so we can add new sub-metrics without migrations. The "official" sub-scores get their own typed columns; everything else lives in JSON.

### `scan_findings`

Individual findings from the engines, surfaced on the report page.

```sql
CREATE TYPE finding_severity AS ENUM (
    'critical', 'high', 'medium', 'low', 'info'
);

CREATE TYPE finding_engine AS ENUM (
    'semgrep', 'trivy', 'scorecard', 'lint', 'complexity', 'duplication', 'hygiene'
);

CREATE TABLE scan_findings (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id       UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    engine        finding_engine NOT NULL,
    severity      finding_severity NOT NULL,
    rule_id       TEXT,                  -- e.g. 'python.lang.security.audit.dangerous-eval'
    title         TEXT NOT NULL,
    message       TEXT,                  -- human-readable
    file_path     TEXT,
    line_number   INTEGER,
    code_snippet  TEXT,                  -- few lines around the finding
    raw_json      JSONB,                 -- full engine output for this finding
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_findings_scan ON scan_findings(scan_id);
CREATE INDEX idx_findings_severity ON scan_findings(scan_id, severity);
```

Findings can be thousands per scan on big repos. We cap at 1000 per engine in the worker; the rest stay in the raw R2 JSON.

### `formula_versions`

Published formula versions for traceability.

```sql
CREATE TABLE formula_versions (
    version       TEXT PRIMARY KEY,      -- 'v1.0', 'v1.1', 'v2.0'
    published_at  TIMESTAMPTZ NOT NULL,
    spec_url      TEXT NOT NULL,         -- link to formula repo at that tag
    summary       TEXT,                  -- one-line description
    is_active     BOOLEAN DEFAULT FALSE  -- only one row TRUE at a time
);

-- Seed
INSERT INTO formula_versions (version, published_at, spec_url, summary, is_active)
VALUES ('v1.0', NOW(), 'https://github.com/santosh3743/stackhealth/tree/main/packages/formula-spec/tree/v1.0',
        'Initial formula. Security 30, Quality 25, Hygiene 25, Community 20.', TRUE);
```

### `rate_limits`

Simple token-bucket / sliding-window counters. Could live in Redis only, but having it in Postgres makes debugging easier.

```sql
CREATE TABLE rate_limits (
    key            TEXT PRIMARY KEY,      -- 'ip:1.2.3.4', 'repo:owner/name'
    count          INTEGER NOT NULL DEFAULT 0,
    window_start   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

In practice we'll use Redis for hot-path rate limiting and only use this table for analytics / debugging.

---

## Future tables (Phase 2+, not in MVP)

```sql
-- Phase 2: user accounts (GitHub OAuth)
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id       BIGINT UNIQUE NOT NULL,
    github_login    TEXT NOT NULL,
    avatar_url      TEXT,
    email           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Phase 2: claimed repos (a user verifies they own/maintain a repo)
CREATE TABLE repo_claims (
    user_id    UUID REFERENCES users(id),
    repo_id    UUID REFERENCES repos(id),
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, repo_id)
);

-- Phase 3: comments on reports
CREATE TABLE scan_comments (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id       UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    user_id       UUID NOT NULL REFERENCES users(id),
    parent_id     UUID REFERENCES scan_comments(id),
    body          TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Phase 3: false-positive markings by repo owners
CREATE TABLE finding_disputes (
    finding_id   UUID PRIMARY KEY REFERENCES scan_findings(id),
    user_id      UUID NOT NULL REFERENCES users(id),
    reason       TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## Sizing estimate

A scan record averages ~2 KB. Findings average ~500 bytes; a big repo might have 500 findings = 250 KB.

| Scans | Storage |
|-------|---------|
| 1,000 | ~250 MB |
| 10,000 | ~2.5 GB |
| 100,000 | ~25 GB |

Neon free tier (0.5 GB) covers ~2,000 scans comfortably. We'd hit the free tier limit around 4–5k scans, at which point we upgrade to Neon paid ($19/month, 10 GB).

Findings are the heaviest. If storage becomes an issue, we keep the last 5 scans per repo with full findings and prune older ones to summary only (raw artifacts stay on R2 forever).

---

## Migration strategy

- Initial migration: all MVP tables in one Alembic revision (`001_initial.py`).
- Each new feature gets its own revision. Branch staging via Neon to test migrations.
- **No destructive migrations without explicit confirmation.** Alembic autogenerate-then-review.
- All migrations reviewed by reading the SQL before running. (You know this from Zeron's migration-validator agent.)
