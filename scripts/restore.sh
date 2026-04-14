#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root

if [[ $# -lt 1 ]]; then
    echo "Uso: scripts/restore.sh <arquivo-backup.tar.gz> [--target-dir <dir>] [--yes]" >&2
    exit 1
fi

backup_file="$1"
shift
target_dir="${PROJECT_ROOT}"
auto_confirm="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target-dir)
            target_dir="$2"
            shift 2
            ;;
        --yes)
            auto_confirm="true"
            shift
            ;;
        *)
            echo "Argumento invalido: $1" >&2
            exit 1
            ;;
    esac
done

if [[ ! -f "${backup_file}" ]]; then
    echo "Arquivo de backup nao encontrado: ${backup_file}" >&2
    exit 1
fi

target_dir="$(cd "$(dirname "${target_dir}")" && pwd)/$(basename "${target_dir}")"
tmp_dir="$(mktemp -d)"
extract_dir="${tmp_dir}/extract"
mkdir -p "${extract_dir}" "${target_dir}" "${target_dir}/data" "${target_dir}/data/exports" "${target_dir}/data/backups"

cleanup() {
    rm -rf "${tmp_dir}"
}
trap cleanup EXIT

tar -xzf "${backup_file}" -C "${extract_dir}"

manifest_file="${extract_dir}/backup_manifest.env"
if [[ ! -f "${manifest_file}" ]]; then
    echo "Manifesto do backup nao encontrado." >&2
    exit 1
fi

# shellcheck disable=SC1090
source "${manifest_file}"

if [[ "${target_dir}" == "${PROJECT_ROOT}" ]]; then
    if ss -ltn 2>/dev/null | grep -qE '127\.0\.0\.1:(8000|8501)'; then
        echo "Existem servicos rodando nas portas 8000/8501. Pare a stack antes do restore." >&2
        exit 1
    fi

    if [[ "${auto_confirm}" != "true" ]]; then
        echo "Restore no diretorio atual vai sobrescrever .env, banco e exportacoes."
        echo "Use --yes para confirmar explicitamente."
        exit 1
    fi

    safety_name="pre_restore_$(timestamp_utc).tar.gz"
    safety_path="${BACKUP_DIR}/${safety_name}"
    safety_tmp="${tmp_dir}/safety"
    mkdir -p "${safety_tmp}/data/exports"
    [[ -f "${PROJECT_ROOT}/.env" ]] && cp "${PROJECT_ROOT}/.env" "${safety_tmp}/.env"
    if db_path="$(resolve_sqlite_db_path 2>/dev/null)" && [[ -f "${db_path}" ]]; then
        cp "${db_path}" "${safety_tmp}/data/$(basename "${db_path}")"
    fi
    if [[ -d "${PROJECT_ROOT}/data/exports" ]]; then
        cp -R "${PROJECT_ROOT}/data/exports/." "${safety_tmp}/data/exports/" 2>/dev/null || true
    fi
    tar -czf "${safety_path}" -C "${safety_tmp}" .
    echo "Snapshot de seguranca criada em: ${safety_path}"
fi

if [[ -f "${extract_dir}/.env" ]]; then
    cp "${extract_dir}/.env" "${target_dir}/.env"
fi

if [[ "${DB_MODE:-}" == "sqlite" && -n "${DB_SNAPSHOT_NAME:-}" && -f "${extract_dir}/data/${DB_SNAPSHOT_NAME}" ]]; then
    db_target="${target_dir}/data/${DB_SNAPSHOT_NAME}"
    cp "${extract_dir}/data/${DB_SNAPSHOT_NAME}" "${db_target}"
    if [[ -f "${extract_dir}/data/${DB_SNAPSHOT_NAME}-wal" ]]; then
        cp "${extract_dir}/data/${DB_SNAPSHOT_NAME}-wal" "${db_target}-wal"
    fi
    if [[ -f "${extract_dir}/data/${DB_SNAPSHOT_NAME}-journal" ]]; then
        cp "${extract_dir}/data/${DB_SNAPSHOT_NAME}-journal" "${db_target}-journal"
    fi
fi

rm -rf "${target_dir}/data/exports"
mkdir -p "${target_dir}/data/exports"
if [[ -d "${extract_dir}/data/exports" ]]; then
    cp -R "${extract_dir}/data/exports/." "${target_dir}/data/exports/" 2>/dev/null || true
fi

if [[ -x "${target_dir}/.venv/bin/python" && -f "${target_dir}/alembic.ini" ]]; then
    (
        cd "${target_dir}"
        .venv/bin/python -m alembic upgrade head >/dev/null
    )
fi

echo "Restore concluido com sucesso."
echo "Destino: ${target_dir}"
echo "Backup restaurado: ${backup_file}"
