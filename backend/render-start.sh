#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

: "${DATABASE_URL:?Set DATABASE_URL in the Render environment}"
: "${JWT_SECRET:?Set JWT_SECRET in the Render environment}"

if [[ ! -x .venv/bin/alembic || ! -x .venv/bin/uvicorn ]]; then
  printf 'TalentHub: dependencies are missing. Run render-build.sh first.\n' >&2
  exit 1
fi

.venv/bin/alembic upgrade head
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
