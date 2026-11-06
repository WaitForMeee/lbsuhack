"""Exercise the Render shell entrypoint with a broken uv wrapper in PATH."""

import os
import shutil
import subprocess
from pathlib import Path

BUILD_SCRIPT = Path(__file__).resolve().parents[2] / "render-build.sh"


def executable(path, source):
    path.write_text(source)
    path.chmod(0o755)


def test_build_bootstraps_uv_when_render_wrapper_has_no_binary(tmp_path):
    backend = tmp_path / "backend"
    backend.mkdir()
    shutil.copy2(BUILD_SCRIPT, backend / BUILD_SCRIPT.name)
    tools = tmp_path / "bin"
    tools.mkdir()
    trace = tmp_path / "uv.trace"
    wrapper_trace = tmp_path / "wrapper.trace"
    real_uv = tmp_path / "installed-uv"
    executable(
        tools / "uv",
        """#!/usr/bin/env bash
printf 'called' > "$WRAPPER_TRACE"
printf '/home/render/envwrappers/uv: line 100: uv: command not found\\n' >&2
exit 127
""",
    )
    # Stand in for Python/venv/pip; exercise the real build script, without network.
    executable(
        tools / "python",
        """#!/usr/bin/env bash
set -eu
if [[ "$1 $2" == '-m venv' ]]; then
  mkdir -p "$3/bin"
  cp "$0" "$3/bin/python"
elif [[ "$1 $2 $3" == '-m pip install' ]]; then
  cp "$INSTALLED_UV" "$(dirname "$0")/uv"
else
  exit 99
fi
""",
    )
    executable(
        real_uv,
        """#!/usr/bin/env bash
set -eu
printf '%s\\n' "$UV_PROJECT_ENVIRONMENT" "$*" > "$UV_TRACE"
""",
    )
    result = subprocess.run(
        ["bash", str(backend / BUILD_SCRIPT.name)],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": str(tools) + os.pathsep + os.environ["PATH"],
            "UV_TRACE": str(trace),
            "WRAPPER_TRACE": str(wrapper_trace),
            "INSTALLED_UV": str(real_uv),
        },
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert not wrapper_trace.exists(), "Render wrapper must be bypassed"
    assert trace.read_text().splitlines() == [
        str(backend / ".venv"),
        "sync --locked --no-dev",
    ]
