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

if ss -ltn "( sport = :8501 )" | grep -q ":8501"; then
    echo "A porta 8501 ja esta em uso." >&2
    exit 1
fi

source .venv/bin/activate
echo "Iniciando admin em http://127.0.0.1:8501"
python -m streamlit run streamlit_app/Home.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false > "${PROJECT_ROOT}/data/logs/ec2_admin.log" 2>&1 &
echo $! > "${RUN_DIR}/ec2_admin.pid"
echo "PID do admin: $(cat "${RUN_DIR}/ec2_admin.pid")"
