# Operacao padronizada da EC2

# 1. Entre na instancia EC2 por SSH
# ssh -i /caminho/para/insightflow-key.pem ubuntu@SEU_IP_PUBLICO

# 2. Entre no projeto dentro da EC2
cd ~/apps/agente-feedback-conversacional

# 3. Bootstrap da maquina (primeira vez)
scripts/ec2_bootstrap.sh

# 4. Setup da aplicacao
scripts/ec2_setup_app.sh

# 5. Validar status
scripts/ec2_status.sh

# 6. Opcional: dados de exemplo
source .venv/bin/activate && python scripts/seed_demo_data.py

# 7. Subir API para teste
scripts/ec2_run_api.sh

# 8. Em outro terminal SSH, subir admin para teste
scripts/ec2_run_admin.sh

# 9. Conferir status
scripts/ec2_status.sh

# 10. Ver logs
scripts/ec2_logs.sh

# 11. Sincronizar IP publico da EC2 no .env
scripts/ec2_sync_public_ip.sh

# Se for usar hostname/HTTPS, adicione no .env antes:
# EC2_PUBLIC_HOSTNAME=insightflow.ddns.net
# EC2_PUBLIC_SCHEME=https
# EC2_ADMIN_BASE_PATH=/admin

# 12. Instalar servicos permanentes
scripts/ec2_install_systemd.sh

# 13. Parar processos manuais quando terminar
scripts/ec2_stop.sh

# 14. Backup operacional da instancia
scripts/backup.sh ec2-manual

# 15. Validar restore em ambiente temporario
scripts/backup_verify.sh data/backups/insightflow_backup_<timestamp>_ec2-manual.tar.gz

# URLs esperadas no teste inicial
# API local: http://127.0.0.1:8000
# Admin local: http://127.0.0.1:8501/admin
