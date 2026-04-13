#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SYSTEMD_DIR="${PROJECT_ROOT}/deploy/systemd"

echo "Instalando units systemd..."
sudo cp "${SYSTEMD_DIR}/insightflow-api.service" /etc/systemd/system/insightflow-api.service
sudo cp "${SYSTEMD_DIR}/insightflow-admin.service" /etc/systemd/system/insightflow-admin.service

echo "Recarregando systemd..."
sudo systemctl daemon-reload

echo "Habilitando servicos..."
sudo systemctl enable insightflow-api
sudo systemctl enable insightflow-admin

echo "Reiniciando servicos..."
sudo systemctl restart insightflow-api
sudo systemctl restart insightflow-admin

echo "Status atual:"
sudo systemctl status insightflow-api --no-pager || true
sudo systemctl status insightflow-admin --no-pager || true
