#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "${DOMAIN}" || -z "${EMAIL}" ]]; then
    echo "Uso: scripts/ec2_install_https.sh <dominio> <email>" >&2
    echo "Exemplo: scripts/ec2_install_https.sh app.seudominio.com voce@seudominio.com" >&2
    exit 1
fi

echo "Instalando Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

echo "Solicitando certificado para ${DOMAIN}..."
sudo certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${EMAIL}" --redirect

echo "HTTPS configurado. Teste https://${DOMAIN}"
