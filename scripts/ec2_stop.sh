#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/data/run"

stop_pid_file() {
    local name="$1"
    local pid_file="${RUN_DIR}/${name}.pid"
    local pid=""

    if [[ -f "${pid_file}" ]]; then
        pid="$(cat "${pid_file}")"
    fi

    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
        echo "Parando ${name} (pid ${pid})"
        kill "${pid}" 2>/dev/null || true
    fi

    rm -f "${pid_file}"
}

stop_pid_file "ec2_api"
stop_pid_file "ec2_admin"

pkill -f "uvicorn app.main:app --host 127.0.0.1 --port 8000" 2>/dev/null || true
pkill -f "streamlit run streamlit_app/Home.py --server.port 8501" 2>/dev/null || true

echo "Processos manuais da EC2 finalizados."
