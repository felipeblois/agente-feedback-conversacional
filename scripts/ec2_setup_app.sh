#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/data/run"
LOG_DIR="${PROJECT_ROOT}/data/logs"

cd "${PROJECT_ROOT}"
mkdir -p "${RUN_DIR}" "${LOG_DIR}" data

if [[ ! -f ".env" ]]; then
    echo "Arquivo .env nao encontrado em ${PROJECT_ROOT}." >&2
    echo "Copie .env.example para .env e ajuste as credenciais antes de continuar." >&2
    exit 1
fi

if [[ ! -d ".venv" ]]; then
    echo "Criando virtualenv da EC2..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Atualizando pip..."
pip install --upgrade pip

echo "Instalando dependencias do projeto..."
pip install .

echo "Aplicando migrations..."
python -m alembic upgrade head

echo "Setup da aplicacao concluido."
