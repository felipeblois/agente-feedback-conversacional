#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"
RUN_DIR="${PROJECT_ROOT}/data/run"
LOG_DIR="${PROJECT_ROOT}/data/logs"

ensure_linux() {
    if [[ -z "${BASH_VERSION:-}" ]]; then
        echo "Este projeto deve ser operado via bash no WSL/Linux." >&2
        exit 1
    fi
}

ensure_project_root() {
    cd "${PROJECT_ROOT}"
    mkdir -p "${RUN_DIR}" "${LOG_DIR}"
}

ensure_venv() {
    if [[ ! -x "${VENV_PYTHON}" ]]; then
        echo "Virtualenv Linux nao encontrada em ${VENV_PYTHON}." >&2
        echo "Execute 'make setup' dentro do WSL para recriar o ambiente." >&2
        exit 1
    fi
}

run_python_module() {
    local module="$1"
    shift
    "${VENV_PYTHON}" -m "${module}" "$@"
}

ensure_database_schema() {
    echo "Garantindo banco atualizado via Alembic..."
    run_python_module alembic upgrade head
}

write_pid() {
    local name="$1"
    local pid="$2"
    echo "${pid}" > "${RUN_DIR}/${name}.pid"
}

read_pid() {
    local name="$1"
    local pid_file="${RUN_DIR}/${name}.pid"
    if [[ -f "${pid_file}" ]]; then
        cat "${pid_file}"
    fi
}

remove_pid() {
    local name="$1"
    rm -f "${RUN_DIR}/${name}.pid"
}

is_pid_running() {
    local pid="$1"
    [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

find_pid_by_pattern() {
    local pattern="$1"
    pgrep -f "${pattern}" | head -n 1 || true
}

find_listener_pid_by_port() {
    local port="$1"
    ss -ltnp 2>/dev/null | sed -n "s/.*127.0.0.1:${port} .*pid=\([0-9]\+\).*/\1/p" | head -n 1
}

ensure_port_free() {
    local port="$1"
    local service_name="$2"
    local pattern="$3"
    local listener_pid

    listener_pid="$(find_listener_pid_by_port "${port}" || true)"
    if [[ -z "${listener_pid}" ]]; then
        return
    fi

    local managed_pid
    managed_pid="$(find_pid_by_pattern "${pattern}")"
    if [[ -n "${managed_pid}" && "${listener_pid}" == "${managed_pid}" ]]; then
        echo "Parando instancia anterior de ${service_name} na porta ${port}..."
        kill "${listener_pid}" 2>/dev/null || true
        sleep 2
        return
    fi

    echo "Porta ${port} ja esta em uso por pid ${listener_pid}. Finalize o processo antes de iniciar ${service_name}." >&2
    exit 1
}
