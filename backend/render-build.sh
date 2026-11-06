#!/usr/bin/env bash
set -Eeuo pipefail

BACKEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BACKEND_DIR"

# Render can expose a uv wrapper without installing the actual binary when
# uv.lock is below the service root. Bootstrap our own copy and bypass PATH.
BUILD_TOOLS_DIR="$BACKEND_DIR/.render-tools"
python -m venv "$BUILD_TOOLS_DIR"
"$BUILD_TOOLS_DIR/bin/python" -m pip install --disable-pip-version-check --no-input "uv==0.11.6"
UV_PROJECT_ENVIRONMENT="$BACKEND_DIR/.venv" "$BUILD_TOOLS_DIR/bin/uv" sync --locked --no-dev
