# Operacao padronizada do projeto

# 1. Sempre entre pelo WSL
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional

# 2. Crie ou atualize o ambiente
make setup

# 3. Valide o ambiente operacional
scripts/doctor.sh

# 4. Opcional: dados de exemplo
make seed

# 5. Suba a stack completa
scripts/start.sh

# 6. Confira o status
scripts/status.sh

# 7. Para encerrar quando terminar
scripts/stop_all.sh

# URLs principais
# API: http://localhost:8000
# Admin: http://localhost:8501
# Docs: http://localhost:8000/docs
