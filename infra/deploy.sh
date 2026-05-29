#!/usr/bin/env bash
# Deploy StackHealth on a single Linux VM. Run from the repo root.
#
# Usage:
#   ./infra/deploy.sh           # build + restart everything
#   ./infra/deploy.sh pull      # git pull first, then build + restart
#   ./infra/deploy.sh logs      # tail all service logs
#   ./infra/deploy.sh status    # show service status
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "✗ .env not found. Copy infra/.env.prod.example to .env and fill it in."
  exit 1
fi

COMPOSE=(docker compose -f infra/docker-compose.prod.yml --env-file .env)

case "${1:-up}" in
  pull)
    git pull
    "${COMPOSE[@]}" up -d --build
    ;;
  up)
    "${COMPOSE[@]}" up -d --build
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  logs)
    "${COMPOSE[@]}" logs -f --tail=200
    ;;
  status)
    "${COMPOSE[@]}" ps
    ;;
  *)
    echo "usage: $0 {up|pull|down|logs|status}"
    exit 1
    ;;
esac
