#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PID=""
FRONTEND_PID=""

fail() {
  printf 'TalentHub: %s\n' "$1" >&2
  exit 1
}

stop_processes() {
  trap - EXIT INT TERM

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]]; then
    wait "$BACKEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$FRONTEND_PID" ]]; then
    wait "$FRONTEND_PID" 2>/dev/null || true
  fi
}

command -v uv >/dev/null 2>&1 || fail "uv is not installed. See https://docs.astral.sh/uv/."
command -v npm >/dev/null 2>&1 || fail "npm is not installed. Install Node.js 22.12 or newer."
if [[ ! -f "$BACKEND_DIR/.env" ]] && { [[ -z "${DATABASE_URL:-}" ]] || [[ -z "${JWT_SECRET:-}" ]]; }; then
  fail "backend/.env is missing. Copy backend/.env.example and fill in its values."
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  printf 'Installing frontend dependencies...\n'
  (cd "$FRONTEND_DIR" && npm ci)
fi

printf 'Applying database migrations...\n'
(cd "$BACKEND_DIR" && uv run --locked alembic upgrade head)

trap stop_processes EXIT INT TERM

printf 'Starting API at http://127.0.0.1:8000...\n'
(cd "$BACKEND_DIR" && uv run --locked uvicorn app.main:app --reload) &
BACKEND_PID=$!

printf 'Starting frontend at http://localhost:5173...\n'
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

printf '\nTalentHub is starting. Press Ctrl+C to stop both processes.\n\n'

while kill -0 "$BACKEND_PID" 2>/dev/null && kill -0 "$FRONTEND_PID" 2>/dev/null; do
  sleep 1
done

set +e
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  wait "$BACKEND_PID"
  EXIT_STATUS=$?
else
  wait "$FRONTEND_PID"
  EXIT_STATUS=$?
fi
set -e

exit "$EXIT_STATUS"
