#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root

label="${1:-manual}"
label="$(echo "${label}" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9._-' '-')"
label="${label#-}"
label="${label%-}"
timestamp="$(timestamp_utc)"
archive_name="insightflow_backup_${timestamp}_${label}.tar.gz"
archive_path="${BACKUP_DIR}/${archive_name}"
tmp_dir="$(mktemp -d)"
package_dir="${tmp_dir}/package"
db_mode="external"
db_snapshot_name=""
db_path=""
exports_count=0

cleanup() {
    rm -rf "${tmp_dir}"
}
trap cleanup EXIT

mkdir -p "${package_dir}/data/exports"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    cp "${PROJECT_ROOT}/.env" "${package_dir}/.env"
fi

if db_path="$(resolve_sqlite_db_path 2>/dev/null)"; then
    db_mode="sqlite"
    if [[ ! -f "${db_path}" ]]; then
        echo "Banco SQLite nao encontrado em ${db_path}." >&2
        exit 1
    fi

    db_snapshot_name="$(basename "${db_path}")"
    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "${db_path}" ".backup '${package_dir}/data/${db_snapshot_name}'"
    else
        if ss -ltn 2>/dev/null | grep -qE '127\.0\.0\.1:(8000|8501)'; then
            echo "sqlite3 nao encontrado e a stack parece ativa. Pare a aplicacao antes do backup ou instale sqlite3." >&2
            exit 1
        fi
        echo "sqlite3 nao encontrado; copiando o arquivo do banco diretamente."
        cp "${db_path}" "${package_dir}/data/${db_snapshot_name}"
        for sidecar in "${db_path}-wal" "${db_path}-journal"; do
            if [[ -f "${sidecar}" ]]; then
                cp "${sidecar}" "${package_dir}/data/$(basename "${sidecar}")"
            fi
        done
    fi
else
    echo "DATABASE_URL nao usa SQLite. Este backup vai incluir apenas .env e exportacoes." >&2
fi

if [[ -d "${PROJECT_ROOT}/data/exports" ]]; then
    cp -R "${PROJECT_ROOT}/data/exports/." "${package_dir}/data/exports/" 2>/dev/null || true
    exports_count="$(find "${PROJECT_ROOT}/data/exports" -maxdepth 1 -type f -name '*.pdf' | wc -l | tr -d ' ')"
fi

cat > "${package_dir}/backup_manifest.env" <<EOF
BACKUP_CREATED_AT_UTC=${timestamp}
BACKUP_LABEL=${label}
APP_ENV=${APP_ENV:-$(grep -E '^APP_ENV=' "${PROJECT_ROOT}/.env" | tail -n 1 | cut -d= -f2- || echo local)}
INSTANCE_ID=${INSTANCE_ID:-$(grep -E '^INSTANCE_ID=' "${PROJECT_ROOT}/.env" | tail -n 1 | cut -d= -f2- || echo unknown)}
INSTANCE_NAME=${INSTANCE_NAME:-$(grep -E '^INSTANCE_NAME=' "${PROJECT_ROOT}/.env" | tail -n 1 | cut -d= -f2- || echo unknown)}
DATABASE_URL=$(resolve_database_url)
DB_MODE=${db_mode}
DB_SNAPSHOT_NAME=${db_snapshot_name}
EXPORTS_COUNT=${exports_count}
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
EOF

tar -czf "${archive_path}" -C "${package_dir}" .

echo "Backup gerado com sucesso."
echo "Arquivo: ${archive_path}"
echo "Modo do banco: ${db_mode}"
echo "Exportacoes incluídas: ${exports_count}"
