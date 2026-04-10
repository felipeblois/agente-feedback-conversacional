# Agente de Feedback Conversacional - MVP

Agente de feedback conversacional pos-apresentacao e treinamento. Coleta notas e respostas adaptativas dos participantes, analisa com IA e gera insights operacionais.

## Padrao operacional

Este projeto deve ser operado pelo Ubuntu no WSL usando a virtualenv Linux em `.venv`.

Padrao adotado:
- abrir o projeto dentro do WSL
- executar `make` e os scripts em `scripts/`
- nao misturar PowerShell com `.venv/bin/...`

## Requisitos

- WSL com Ubuntu
- Python 3.8+ dentro do WSL
- Ollama opcional para IA local

## Setup rapido

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional
make setup
make db
scripts/doctor.sh
```

## Operacao diaria

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional

# diagnostico do ambiente
scripts/doctor.sh

# backend
scripts/run_api.sh

# streamlit
scripts/run_streamlit.sh

# stack completa
scripts/run_all.sh

# testes
scripts/test.sh
```

## Fluxo de uso

### Criar uma sessao
Acesse o Swagger UI em `http://localhost:8000/docs` e crie uma sessao via `POST /api/v1/sessions`.

### Coletar feedbacks
Compartilhe o link publico `http://localhost:8000/f/{token}` com os participantes.

### Visualizar resultados
Acesse o painel admin em `http://localhost:8501`.

## Comandos disponiveis

| Comando | Descricao |
|---|---|
| `make setup` | Cria venv e instala dependencias |
| `make db` | Inicializa ou atualiza o banco |
| `make run-api` | Sobe o backend FastAPI |
| `make run-streamlit` | Sobe o painel admin |
| `make run` | Sobe backend e admin em background |
| `make test` | Roda os testes |
| `make seed` | Popula com dados de exemplo |
| `scripts/doctor.sh` | Valida o ambiente WSL e a venv |
| `scripts/run_all.sh` | Sobe API e Streamlit no mesmo terminal |
| `scripts/test.sh` | Executa os testes pela venv Linux |

## Estrategia de LLM

1. Ollama local: rode `ollama pull llama3.1:8b`
2. Gemini free tier: configure `GEMINI_API_KEY` no `.env`
3. Regras estaticas: o sistema continua funcional sem LLM

## Stack

- Backend: FastAPI + SQLAlchemy + Alembic + SQLite
- Frontend participante: HTML/CSS/JS
- Dashboard admin: Streamlit
- IA: LiteLLM com Ollama e Gemini
- PDF: FPDF2
