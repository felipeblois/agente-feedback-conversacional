#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root
ensure_venv

run_python_module streamlit run streamlit_app/Home.py --server.port 8501 --server.headless true --browser.gatherUsageStats false
