#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root
ensure_venv
ensure_database_schema
ensure_port_free 8000 "api" "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

cleanup() {
    remove_pid "api"
}

trap cleanup EXIT INT TERM

run_python_module uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
write_pid "api" "$!"
wait
