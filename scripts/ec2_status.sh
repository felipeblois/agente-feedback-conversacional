#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/data/run"

show_process() {
    local name="$1"
    local port="$2"
    local pid_file="${RUN_DIR}/${name}.pid"
    local pid=""

    if [[ -f "${pid_file}" ]]; then
        pid="$(cat "${pid_file}")"
    fi

    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
        echo "${name}: rodando (pid ${pid})"
    else
        echo "${name}: parado"
    fi

    if ss -ltn "( sport = :${port} )" | grep -q ":${port}"; then
        echo "porta ${port}: em uso"
    else
        echo "porta ${port}: livre"
    fi
}

echo "Status operacional da EC2"
echo "Projeto: ${PROJECT_ROOT}"
show_process "ec2_api" "8000"
show_process "ec2_admin" "8501"
