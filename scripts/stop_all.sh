#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root

stop_named_process() {
    local name="$1"
    local pid
    pid="$(read_pid "${name}" || true)"
    if is_pid_running "${pid}"; then
        echo "Parando ${name} (pid ${pid})"
        kill "${pid}" 2>/dev/null || true
    fi
    remove_pid "${name}"
}

stop_named_process "api"
stop_named_process "streamlit"

pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" 2>/dev/null || true
pkill -f "streamlit run streamlit_app/Home.py" 2>/dev/null || true

echo "Stack local finalizada."
