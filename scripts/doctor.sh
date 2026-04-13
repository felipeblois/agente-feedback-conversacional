#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root
ensure_venv
ensure_database_schema

echo "Projeto: ${PROJECT_ROOT}"
echo "Python: $("${VENV_PYTHON}" --version 2>&1)"
echo "Executavel: ${VENV_PYTHON}"

required_paths=(
    "app/main.py"
    "streamlit_app/Home.py"
    "alembic.ini"
    ".env"
)

for path in "${required_paths[@]}"; do
    if [[ -e "${PROJECT_ROOT}/${path}" ]]; then
        echo "OK: ${path}"
    else
        echo "FALTA: ${path}" >&2
        exit 1
    fi
done

echo "Alembic current:"
run_python_module alembic current

echo "Diagnostico operacional concluido."
echo "Banco: migrations sao aplicadas automaticamente por scripts/run_api.sh e scripts/run_all.sh"
