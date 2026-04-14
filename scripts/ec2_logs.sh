#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

target="${1:-all}"

show_file() {
    local title="$1"
    local path="$2"
    echo "===== ${title} ====="
    if [[ -f "${path}" ]]; then
        tail -n 100 "${path}"
    else
        echo "Arquivo nao encontrado: ${path}"
    fi
}

case "${target}" in
    api)
        show_file "API" "${PROJECT_ROOT}/data/logs/ec2_api.log"
        ;;
    admin)
        show_file "ADMIN" "${PROJECT_ROOT}/data/logs/ec2_admin.log"
        ;;
    nginx)
        echo "===== NGINX ACCESS ====="
        sudo tail -n 100 /var/log/nginx/access.log
        echo "===== NGINX ERROR ====="
        sudo tail -n 100 /var/log/nginx/error.log
        ;;
    all)
        show_file "API" "${PROJECT_ROOT}/data/logs/ec2_api.log"
        show_file "ADMIN" "${PROJECT_ROOT}/data/logs/ec2_admin.log"
        echo "===== NGINX ACCESS ====="
        sudo tail -n 50 /var/log/nginx/access.log
        echo "===== NGINX ERROR ====="
        sudo tail -n 50 /var/log/nginx/error.log
        ;;
    *)
        echo "Uso: scripts/ec2_logs.sh [api|admin|nginx|all]" >&2
        exit 1
        ;;
esac
