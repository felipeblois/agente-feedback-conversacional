.PHONY: setup db run-api run-streamlit run test seed backup restore verify-backup clean help

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

help: ## Mostra ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Cria venv, instala dependencias e aplica migrations
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	cp -n .env.example .env 2>/dev/null || true
	mkdir -p data data/logs
	$(PYTHON) -m alembic upgrade head
	@echo "Setup completo com banco atualizado. Ative o venv: source $(VENV)/bin/activate"

db: ## Inicializa banco de dados (migrações)
	$(PYTHON) -m alembic upgrade head
	@echo "✅ Banco de dados criado/atualizado"

run-api: ## Sobe o backend FastAPI
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run-streamlit: ## Sobe o painel admin Streamlit
	$(PYTHON) -m streamlit run streamlit_app/Home.py --server.port 8501

run: ## Sobe backend + streamlit (background)
	@echo "🚀 Iniciando backend e Streamlit..."
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload &
	$(PYTHON) -m streamlit run streamlit_app/Home.py --server.port 8501 &
	@echo "✅ Backend: http://localhost:8000"
	@echo "✅ Admin:   http://localhost:8501"
	@echo "📖 API Docs: http://localhost:8000/docs"

test: ## Roda testes
	$(PYTHON) -m alembic upgrade head
	$(PYTHON) -m pytest tests/ -v

backup: ## Gera backup da instancia local (use BACKUP_LABEL=nome opcional)
	bash scripts/backup.sh $(BACKUP_LABEL)

restore: ## Restaura backup no projeto atual (use BACKUP_FILE=caminho e confirme com RESTORE_ARGS=--yes)
	bash scripts/restore.sh $(BACKUP_FILE) $(RESTORE_ARGS)

verify-backup: ## Valida um backup em restore temporario (use BACKUP_FILE=caminho)
	bash scripts/backup_verify.sh $(BACKUP_FILE)

seed: ## Popula banco com dados de exemplo
	$(PYTHON) scripts/seed_demo_data.py

clean: ## Limpa banco e cache
	rm -f data/*.db data/*.db-journal data/*.db-wal
	rm -rf data/logs/*
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpeza completa"
