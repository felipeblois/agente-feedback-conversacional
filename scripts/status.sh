#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root

show_status() {
    local name="$1"
    local pattern="$2"
    local pid detected_pid
    pid="$(read_pid "${name}" || true)"
    if is_pid_running "${pid}"; then
        echo "${name}: running (pid ${pid})"
        return
    fi

    detected_pid="$(find_pid_by_pattern "${pattern}")"
    if is_pid_running "${detected_pid}"; then
        echo "${name}: running sem pidfile (pid ${detected_pid})"
    else
        echo "${name}: stopped"
    fi
}

show_status "api" "uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
show_status "streamlit" "streamlit run streamlit_app/Home.py"

echo "--- portas ---"
ss -ltnp | grep 127.0.0.1:8000 || true
ss -ltnp | grep 127.0.0.1:8501 || true
