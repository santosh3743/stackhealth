# Contributing to StackHealth

Thank you for considering a contribution. StackHealth is an open code
health benchmark — every weight, threshold, and engine is meant to be
inspectable and improvable by people who know the field better than the
maintainer does.

Three kinds of contributions are especially welcome:

1. **Bug reports** with a minimal reproduction (a public repo URL +
   the unexpected score is enough).
2. **Pull requests** that fix bugs, improve docs, or add tests.
3. **Proposals against the scoring formula** — these go through a
   public RFC process described below.

For larger features or anything that changes the formula, please open a
discussion or draft issue **before** writing code. It saves both of us
time if the direction is wrong.

---

## Code of Conduct

By participating, you agree to abide by the
[Code of Conduct](./CODE_OF_CONDUCT.md). Be kind, be specific, and assume
the other person has good intentions.

---

## Repository layout

```
StackHealth/
├── apps/
│   ├── web/                       Next.js 15 frontend (TypeScript)
│   └── api/                       FastAPI + RQ worker (Python 3.12)
│       ├── stackhealth/
│       │   ├── api/               HTTP routes
│       │   ├── engines/           Scanning engines (semgrep, trivy, …)
│       │   ├── formula/           The open scoring formula (v1.py)
│       │   ├── models/            SQLAlchemy models
│       │   ├── schemas/           Pydantic request/response shapes
│       │   └── worker/            RQ jobs and pipeline
│       └── alembic/versions/      Database migrations
├── packages/
│   └── formula-spec/              Frozen, machine-readable formula spec
├── docs/                          Vision, methodology, roadmap, API design
├── infra/                         Dockerfile + compose + Caddyfile
├── scripts/                       Helper shell scripts
└── .github/workflows/             CI + deploy
```

## Local development

### Prerequisites

| Tool | Version | Why |
|---|---|---|
| Node.js | 20+ | Web app + jscpd |
| pnpm | 9+ | JS package manager |
| Python | 3.12+ | API + worker |
| `uv` | latest | Python package manager |
| Docker | 24+ | Postgres + Redis + production-style local run |
| Git | 2.30+ | Shallow clone with filter |

The worker also needs these binaries on its PATH (already bundled into
the Docker image): `git`, `cloc`, `semgrep`, `trivy`, `lizard`,
`scorecard`, `jscpd`. For purely local Python development you can use
Docker to skip installing them.

### One-time setup

```bash
git clone https://github.com/santosh3743/stackhealth.git
cd stackhealth
./scripts/setup.sh        # copies .env.example → .env.local, installs deps
```

Then fill in `apps/api/.env.local`:
- `DATABASE_URL` — point at your local Postgres (or use Docker Compose)
- `REDIS_URL` — local Redis
- `GITHUB_TOKEN` — optional, but lifts GitHub's anonymous 60/hr cap

### Run everything in containers (recommended)

```bash
docker compose -f infra/docker-compose.prod.yml --env-file .env up -d --build
```

That spins up Postgres, Redis, the API, the worker, the Next.js web,
and Caddy (for TLS). See [`infra/README.md`](./infra/README.md).

### Run the parts directly (without Docker)

```bash
# Terminal 1: web
cd apps/web && pnpm dev                    # http://localhost:3000

# Terminal 2: API
cd apps/api && uv run uvicorn stackhealth.api.main:app --reload --port 8000

# Terminal 3: worker
cd apps/api && uv run python -m stackhealth.worker.main
```

### Migrations

```bash
cd apps/api
uv run alembic upgrade head                            # apply all migrations
uv run alembic revision --autogenerate -m "describe"   # create a new one
```

Review the generated SQL before committing.

### Tests

```bash
cd apps/api && uv run pytest -q
cd apps/web && pnpm test    # if/when the web suite exists
```

For a frontend change, also run:

```bash
cd apps/web && pnpm typecheck && pnpm lint && pnpm build
```

---

## Code style

### Python (apps/api)

- **Format + lint**: `uv run ruff format . && uv run ruff check . --fix`
- 100-char line length, target Python 3.12.
- Type hints everywhere; Pydantic v2 for boundary schemas.
- Public functions get a one-paragraph docstring; private helpers don't
  need one unless the *why* is non-obvious.

### TypeScript (apps/web)

- **Format + lint**: `pnpm lint && pnpm format`
- Strict TypeScript; no `any` without a comment explaining why.
- Server components for SSR pages; client components only when state or
  effects are needed (annotated with `"use client"`).
- Tailwind utilities preferred over hand-rolled CSS.

### Commits

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(routing): replace github.com with stackhealth.dev for instant reports
fix(api): allow PATCH in CORS so mid-scan email opt-in actually works
docs: clarify scorecard timeout in scoring methodology
```

Types we use: `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`,
`ci`, `build`, `style`.

### Pull requests

Use the PR template that appears when you open one. The short version:

- Tie the PR to an issue or a clear "why".
- Keep PRs focused — one concern per PR. Bug fixes and refactors are
  separate PRs.
- Tests pass (`pytest`, `pnpm typecheck`, `pnpm build`) before review.
- If you change the scoring formula, see the **Changing the formula**
  section below.
- Screenshots for UI changes (before / after).

---

## Changing the scoring formula

The scoring formula is the heart of the project, so changes follow a
slightly more formal process than the rest of the code.

1. **Open an issue first** describing the change you're proposing,
   the rationale, and the calibration data behind it (which repos
   would score higher/lower, by how much).
2. **Edit all three places in lockstep**:
   - `apps/api/stackhealth/formula/v1.py` (the executable formula)
   - `docs/03-SCORING-METHODOLOGY.md` (the human-readable spec)
   - `packages/formula-spec/v1.0.md` (the frozen machine-readable spec)
3. **Update tests** in `apps/api/tests/test_formula.py` — the worked
   examples must continue to compute to the same values, and any new
   thresholds need new test cases.
4. **Note the change in CHANGELOG.md** under the right version line:
   - `v1.0.x` → bug fixes only (same inputs must still produce the
     same score).
   - `v1.x` → threshold tweaks, new optional engines. Old scans are
     NOT re-scored.
   - `v2` → structural changes. Preceded by a public RFC.

We will reject formula PRs that don't update all three sync targets or
that lack calibration data.

---

## Reporting bugs

Use the **Bug report** issue template. The most useful bug report
includes:

- A public GitHub URL that reproduces the issue.
- What you expected vs. what you got.
- The scan ID (visible in the URL as `/r/owner/name/<scan_id>`) if
  applicable.
- The `formula_version` of the affected scan.

---

## Reporting security issues

**Please do not open a public issue for a security problem.** See
[SECURITY.md](./SECURITY.md) for the responsible disclosure process.

---

## Discussions vs. issues

- **Discussions** (when enabled in the repo): open-ended questions,
  proposals for new directions, sharing your scan results.
- **Issues**: actionable work — bug reports, concrete feature requests,
  formula change proposals.

If you're not sure which fits, default to a discussion.

---

## Questions?

Open a discussion or email `santosh3743@gmail.com`. For anything
formula-related, please link to the relevant section of
`docs/03-SCORING-METHODOLOGY.md` so we're talking about the same
thing.

Thank you for helping make code health measurement more open.
