# 🎯 Agente de Feedback Conversacional — MVP

Agente de feedback conversacional pós-apresentação/treinamento. Coleta notas e respostas adaptativas dos participantes, analisa com IA e gera insights.

## Requisitos

- Python 3.11+
- WSL (Linux)
- Ollama (opcional, para IA local gratuita)

## Setup rápido

```bash
# 1. Clonar e entrar no projeto
git clone git@github.com:felipeblois/agente-feedback-conversacional.git
cd agente-feedback-conversacional

# 2. Setup (cria venv, instala deps, copia .env)
make setup

# 3. Ativar ambiente virtual
source .venv/bin/activate

# 4. Criar banco de dados
make db

# 5. Subir a aplicação
make run-api        # Backend (porta 8000)
make run-streamlit   # Painel admin (porta 8501)
```

## Uso

### Criar uma sessão
Acesse o Swagger UI em http://localhost:8000/docs e crie uma sessão via POST /api/v1/sessions.

### Coletar feedbacks
Compartilhe o link público (`http://localhost:8000/f/{token}`) com os participantes.

### Visualizar resultados
Acesse o painel admin em http://localhost:8501.

## Comandos disponíveis

| Comando | Descrição |
|---|---|
| `make setup` | Cria venv e instala dependências |
| `make db` | Inicializa/atualiza banco de dados |
| `make run-api` | Sobe o backend FastAPI |
| `make run-streamlit` | Sobe o painel admin |
| `make run` | Sobe tudo (backend + admin) |
| `make test` | Roda os testes |
| `make seed` | Popula com dados de exemplo |
| `make clean` | Limpa banco e cache |

## Estratégia de LLM (custo zero)

1. **Ollama local** (preferencial): instale [Ollama](https://ollama.ai) e rode `ollama pull llama3.1:8b`
2. **Gemini Free Tier** (fallback): crie uma API key gratuita em https://aistudio.google.com/apikey
3. **Regras estáticas** (failsafe): funciona sem nenhum LLM configurado

## Stack

- **Backend:** FastAPI + SQLAlchemy + Alembic + SQLite
- **Frontend participante:** HTML/CSS/JS (chat conversacional)
- **Dashboard admin:** Streamlit
- **IA:** LiteLLM (Ollama + Gemini)
- **PDF:** FPDF2
