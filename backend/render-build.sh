#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

# Render provides uv when the service root contains uv.lock.
command -v uv >/dev/null 2>&1 || { printf 'TalentHub: uv is required. Set Render Root Directory to backend.\n' >&2; exit 1; }
UV_PROJECT_ENVIRONMENT="$BACKEND_DIR/.venv" uv sync --locked --no-dev
