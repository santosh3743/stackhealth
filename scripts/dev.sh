#!/usr/bin/env bash
# Start API, worker, and web for local dev. Ctrl-C stops everything.
set -euo pipefail

cd "$(dirname "$0")/.."

if ! curl -sf -o /dev/null http://127.0.0.1:5432 2>/dev/null && \
   ! nc -z localhost 5432 2>/dev/null; then
  echo "✗ Postgres not reachable on localhost:5432. Start it first."
  exit 1
fi

pids=()
trap 'echo "stopping…"; kill ${pids[*]} 2>/dev/null; wait' INT TERM EXIT

echo "==> alembic upgrade"
( cd apps/api && uv run alembic upgrade head ) >/dev/null

echo "==> starting API on :8000"
( cd apps/api && uv run uvicorn stackhealth.api.main:app --reload --host 127.0.0.1 --port 8000 ) &
pids+=($!)

echo "==> starting worker"
( cd apps/api && uv run python -m stackhealth.worker.main ) &
pids+=($!)

echo "==> starting web on :3000"
( cd apps/web && pnpm dev ) &
pids+=($!)

wait
