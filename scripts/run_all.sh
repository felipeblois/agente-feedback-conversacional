#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root
ensure_venv
ensure_database_schema

cleanup() {
    jobs -p | xargs -r kill
}

trap cleanup EXIT INT TERM

echo "Iniciando API em http://127.0.0.1:8000"
run_python_module uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &

echo "Iniciando Streamlit em http://127.0.0.1:8501"
run_python_module streamlit run streamlit_app/Home.py --server.port 8501 &

wait
