#!/usr/bin/env bash
# First-time local setup. Run from the repo root: ./scripts/setup.sh
set -euo pipefail

cd "$(dirname "$0")/.."

echo "==> Checking prerequisites"
command -v node >/dev/null || { echo "✗ Node 20+ required"; exit 1; }
command -v pnpm >/dev/null || { echo "✗ pnpm required: npm i -g pnpm"; exit 1; }
command -v uv >/dev/null || { echo "✗ uv required: https://docs.astral.sh/uv/"; exit 1; }

echo "==> Copying env templates"
for f in .env apps/web/.env apps/api/.env; do
  example="${f}.example"
  [ -f "$example" ] || continue
  target="${f%.example}.local"
  if [ ! -f "$target" ]; then
    cp "$example" "$target"
    echo "  + $target  (please fill in the secrets)"
  else
    echo "  · $target  (kept existing)"
  fi
done

echo "==> Installing web dependencies"
(cd apps/web && pnpm install)

echo "==> Installing api dependencies"
(cd apps/api && uv sync --extra dev)

echo ""
echo "✅ Setup complete."
echo ""
echo "Next steps:"
echo "  1. Fill in apps/api/.env.local (DATABASE_URL, REDIS_URL, GITHUB_TOKEN)"
echo "  2. Run migrations:  cd apps/api && uv run alembic upgrade head"
echo "  3. Start web:       cd apps/web && pnpm dev"
echo "  4. Start API:       cd apps/api && uv run uvicorn stackhealth.api.main:app --reload --port 8000"
echo "  5. Start worker:    cd apps/api && uv run python -m stackhealth.worker.main"
