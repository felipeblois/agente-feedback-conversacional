#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RUN_DIR="${PROJECT_ROOT}/data/run"

cd "${PROJECT_ROOT}"

if [[ ! -x ".venv/bin/python" ]]; then
    echo "Virtualenv nao encontrada. Rode scripts/ec2_setup_app.sh primeiro." >&2
    exit 1
fi

if [[ ! -f ".env" ]]; then
    echo "Arquivo .env nao encontrado." >&2
    exit 1
fi

mkdir -p "${RUN_DIR}"

if ss -ltn "( sport = :8000 )" | grep -q ":8000"; then
    echo "A porta 8000 ja esta em uso." >&2
    exit 1
fi

source .venv/bin/activate
echo "Iniciando API em http://127.0.0.1:8000"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "${PROJECT_ROOT}/data/logs/ec2_api.log" 2>&1 &
echo $! > "${RUN_DIR}/ec2_api.pid"
echo "PID da API: $(cat "${RUN_DIR}/ec2_api.pid")"
