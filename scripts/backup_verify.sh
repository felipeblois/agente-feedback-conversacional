#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

ensure_linux
ensure_project_root

if [[ $# -lt 1 ]]; then
    echo "Uso: scripts/backup_verify.sh <arquivo-backup.tar.gz>" >&2
    exit 1
fi

backup_file="$1"
if [[ ! -f "${backup_file}" ]]; then
    echo "Arquivo de backup nao encontrado: ${backup_file}" >&2
    exit 1
fi

tmp_root="$(mktemp -d)"
restore_target="${tmp_root}/restore_target"
extract_dir="${tmp_root}/extract"

cleanup() {
    rm -rf "${tmp_root}"
}
trap cleanup EXIT

bash "${PROJECT_ROOT}/scripts/restore.sh" "${backup_file}" --target-dir "${restore_target}" --yes

if [[ ! -f "${restore_target}/.env" ]]; then
    echo "Falha na validacao: .env nao foi restaurado." >&2
    exit 1
fi

mkdir -p "${extract_dir}"
tar -xzf "${backup_file}" -C "${extract_dir}"
manifest_env="${extract_dir}/backup_manifest.env"
if [[ ! -f "${manifest_env}" ]]; then
    echo "Falha na validacao: manifesto do backup nao encontrado." >&2
    exit 1
fi
# shellcheck disable=SC1090
source "${manifest_env}"

if [[ "${DB_MODE:-}" == "sqlite" ]]; then
    restored_db="${restore_target}/data/${DB_SNAPSHOT_NAME}"
    if [[ ! -f "${restored_db}" ]]; then
        echo "Falha na validacao: banco SQLite nao foi restaurado." >&2
        exit 1
    fi
    if command -v sqlite3 >/dev/null 2>&1; then
        integrity="$(sqlite3 "${restored_db}" 'pragma integrity_check;' || true)"
        if [[ "${integrity}" != "ok" ]]; then
            echo "Falha na validacao: integrity_check do SQLite retornou '${integrity}'." >&2
            exit 1
        fi
    fi
fi

echo "Backup validado com sucesso."
echo "Arquivo: ${backup_file}"
echo "Restore de teste: ${restore_target}"
