#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

ensure_linux() {
    if [[ -z "${BASH_VERSION:-}" ]]; then
        echo "Este projeto deve ser operado via bash no WSL/Linux." >&2
        exit 1
    fi
}

ensure_project_root() {
    cd "${PROJECT_ROOT}"
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
