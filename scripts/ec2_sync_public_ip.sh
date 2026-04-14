#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
METADATA_BASE="http://169.254.169.254/latest"
QUIET="false"
RESTART="false"

for arg in "$@"; do
    case "${arg}" in
        --quiet)
            QUIET="true"
            ;;
        --restart)
            RESTART="true"
            ;;
        *)
            echo "Uso: scripts/ec2_sync_public_ip.sh [--quiet] [--restart]" >&2
            exit 1
            ;;
    esac
done

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Arquivo .env nao encontrado em ${ENV_FILE}." >&2
    exit 1
fi

log() {
    if [[ "${QUIET}" != "true" ]]; then
        echo "$@"
    fi
}

read_env_value() {
    local key="$1"
    python3 - "${ENV_FILE}" "${key}" <<'PY'
import re
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
key = sys.argv[2]

if not env_path.exists():
    raise SystemExit(0)

content = env_path.read_text(encoding="utf-8")
match = re.search(rf"^{re.escape(key)}=(.*)$", content, re.MULTILINE)
if not match:
    raise SystemExit(0)

print(match.group(1).strip())
PY
}

METADATA_TOKEN="$(curl -sS -m 5 -X PUT "${METADATA_BASE}/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")"

if [[ -z "${METADATA_TOKEN}" ]]; then
    echo "Nao foi possivel obter token IMDSv2 da EC2." >&2
    exit 1
fi

PUBLIC_IP="$(curl -sS -m 5 -H "X-aws-ec2-metadata-token: ${METADATA_TOKEN}" \
    "${METADATA_BASE}/meta-data/public-ipv4")"

if [[ -z "${PUBLIC_IP}" ]]; then
    echo "Nao foi possivel obter o IP publico da EC2." >&2
    exit 1
fi

PREFERRED_HOST="$(read_env_value "EC2_PUBLIC_HOSTNAME")"
PREFERRED_SCHEME="$(read_env_value "EC2_PUBLIC_SCHEME")"
ADMIN_PATH="$(read_env_value "EC2_ADMIN_BASE_PATH")"

if [[ -z "${PREFERRED_SCHEME}" ]]; then
    if [[ -n "${PREFERRED_HOST}" ]]; then
        PREFERRED_SCHEME="https"
    else
        PREFERRED_SCHEME="http"
    fi
fi

if [[ -z "${ADMIN_PATH}" ]]; then
    ADMIN_PATH="/admin"
fi

if [[ "${ADMIN_PATH}" != /* ]]; then
    ADMIN_PATH="/${ADMIN_PATH}"
fi

if [[ -n "${PREFERRED_HOST}" ]]; then
    BASE_HOST="${PREFERRED_HOST}"
    log "Hostname preferencial detectado no .env: ${PREFERRED_HOST}"
else
    BASE_HOST="${PUBLIC_IP}"
    log "Sem hostname preferencial. Usando IP publico da EC2."
fi

API_URL="${PREFERRED_SCHEME}://${BASE_HOST}"
ADMIN_URL="${PREFERRED_SCHEME}://${BASE_HOST}${ADMIN_PATH}"
PUBLIC_URL="${PREFERRED_SCHEME}://${BASE_HOST}"
CORS_URL="${PREFERRED_SCHEME}://${BASE_HOST}"

python3 - "${ENV_FILE}" "${API_URL}" "${ADMIN_URL}" "${PUBLIC_URL}" "${CORS_URL}" <<'PY'
import re
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
updates = {
    "API_BASE_URL": sys.argv[2],
    "ADMIN_BASE_URL": sys.argv[3],
    "PUBLIC_BASE_URL": sys.argv[4],
    "CORS_ALLOWED_ORIGINS": sys.argv[5],
}

content = env_path.read_text(encoding="utf-8")

for key, value in updates.items():
    pattern = re.compile(rf"^{re.escape(key)}=.*$", re.MULTILINE)
    replacement = f"{key}={value}"
    if pattern.search(content):
        content = pattern.sub(replacement, content)
    else:
        if not content.endswith("\n"):
            content += "\n"
        content += replacement + "\n"

env_path.write_text(content, encoding="utf-8")
PY

log "IP publico detectado: ${PUBLIC_IP}"
log "Atualizado em .env:"
log "  API_BASE_URL=${API_URL}"
log "  ADMIN_BASE_URL=${ADMIN_URL}"
log "  PUBLIC_BASE_URL=${PUBLIC_URL}"
log "  CORS_ALLOWED_ORIGINS=${CORS_URL}"

if [[ "${RESTART}" == "true" ]]; then
    log "Reiniciando servicos da aplicacao..."
    sudo systemctl restart insightflow-api
    sudo systemctl restart insightflow-admin
    sudo systemctl reload nginx
fi
