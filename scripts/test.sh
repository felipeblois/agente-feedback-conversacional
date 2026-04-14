#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root
ensure_venv

run_python_module alembic upgrade head
run_python_module pytest tests/ -v
