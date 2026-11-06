#!/usr/bin/env bash
set -Eeuo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v uv >/dev/null 2>&1 || { printf 'TalentHub: install uv first.\n' >&2; exit 1; }
cd "$PROJECT_ROOT/backend"
uv run --locked alembic upgrade head
exec uv run --locked uvicorn app.main:app --reload
