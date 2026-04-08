# MVP local — Agente de feedback conversacional pós-apresentação

> **Versão:** 2.0 — Atualizado em 2026-04-08
> **Decisões técnicas aprovadas:** Stack revisada com foco em custo zero e UX conversacional

## 1. Objetivo do MVP
Construir um produto local, rodando no notebook, capaz de:

- cadastrar uma sessão de apresentação/treinamento
- gerar um link de resposta para participantes
- coletar uma nota principal e respostas conversacionais adaptativas
- persistir os dados localmente
- resumir feedbacks com IA (custo zero via Ollama local + Gemini Free Tier)
- classificar feedbacks em temas
- exibir dashboard simples para análise
- exportar respostas e resumo

## 2. Escopo da versão 1

### Incluído
- execução local (WSL)
- backend em FastAPI
- banco SQLite
- painel admin em Streamlit
- interface conversacional do participante (Jinja2 + Vanilla JS com fetch)
- integração com LLMs via LiteLLM (Ollama local + Gemini Free Tier)
- fallback com regras estáticas quando LLM indisponível
- sumarização por IA
- classificação temática básica
- export CSV
- export PDF simples (FPDF2)

### Fora do escopo inicial
- autenticação corporativa SSO
- Slack/Teams
- WhatsApp
- multi-tenant real
- benchmark entre empresas
- controle granular de permissões
- deploy em nuvem
- cobrança/pagamento
- fila distribuída
- APIs pagas de LLM (OpenAI, Anthropic)

## 3. Stack técnica

### Backend
- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy
- Alembic
- Pydantic
- LiteLLM

### Frontend do participante
- Templates Jinja2 para renderização server-side inicial
- Vanilla HTML/CSS/JS com chamadas fetch() assíncronas
- Interface estilo chat — sem page reload durante a conversa
- Servido diretamente pelo FastAPI (sem build step)

### Frontend admin (dashboard)
- Streamlit (porta 8501)
- Gráficos e tabelas interativas com Plotly/Pandas

### Banco
- SQLite (WAL mode para melhor concorrência)

### LLM — Estratégia de custo zero (3 camadas)
1. **Ollama (preferencial):** modelos locais gratuitos (Llama 3.1 8B, Qwen 2.5 7B)
2. **Gemini API Free Tier (fallback):** API key gratuita do Google AI Studio (gemini-2.5-flash-lite)
3. **Regras estáticas (failsafe):** perguntas pré-definidas + sumarização por keywords. Produto nunca quebra.

### Utilitários
- Pandas
- python-dotenv
- httpx
- pytest
- pytest-asyncio
- loguru (logging)
- FPDF2 (exportação PDF)

### Ambiente de execução
- WSL (Linux)
- Scripts .sh + Makefile

## 4. Backlog técnico completo

## Epic 1 — Setup do projeto

### História 1.1 — Inicializar repositório
**Objetivo:** criar base do projeto.

#### Tarefas
- criar ambiente virtual (venv)
- criar pyproject.toml com todas as dependências
- configurar .env.example
- configurar .gitignore
- configurar estrutura de pastas
- criar README inicial

#### Critério de aceite
- projeto sobe localmente com comando único
- dependências instaladas sem erro

---

### História 1.2 — Configuração base da aplicação
**Objetivo:** preparar app FastAPI e Streamlit.

#### Tarefas
- criar app FastAPI com rota /health
- configurar uvicorn
- criar app Streamlit inicial
- configurar leitura de variáveis de ambiente
- configurar logs com loguru
- criar Makefile com comandos básicos

#### Critério de aceite
- backend responde /health
- painel Streamlit abre localmente
- `make run-api` e `make run-streamlit` funcionam

---

## Epic 2 — Modelo de dados e persistência

### História 2.1 — Criar schema inicial do banco
**Objetivo:** persistir sessões, participantes, respostas e análises.

#### Tarefas
- definir tabelas principais
- implementar models SQLAlchemy
- configurar engine SQLite com WAL mode
- criar migração inicial com Alembic

#### Critério de aceite
- banco é criado localmente
- tabelas disponíveis após migração

---

### História 2.2 — CRUD de sessão
**Objetivo:** permitir criar e consultar sessões.

#### Tarefas
- criar entidade session/event
- criar endpoint de criação de sessão
- criar endpoint de listagem
- criar endpoint de detalhamento
- gerar public_token com secrets.token_urlsafe(8)

#### Critério de aceite
- admin cria sessão
- sessão aparece no painel
- sessão possui link público

---

## Epic 3 — Fluxo do participante

### História 3.1 — Início da resposta
**Objetivo:** participante acessa link e inicia feedback.

#### Tarefas
- criar rota pública da sessão
- exibir título, descrição e termo curto de privacidade
- capturar nome opcional ou resposta anônima
- criar registro do participante/resposta
- implementar template HTML com interface de chat (Jinja2 + Vanilla JS)

#### Critério de aceite
- participante acessa link e inicia resposta sem erro
- interface renderiza como chat conversacional

---

### História 3.2 — Pergunta principal de score
**Objetivo:** coletar score inicial.

#### Tarefas
- implementar pergunta principal (0 a 10 ou 1 a 5)
- persistir score via chamada fetch() assíncrona
- registrar timestamp
- atualizar interface sem page reload

#### Critério de aceite
- score salvo corretamente no banco
- transição suave para próxima pergunta (animação CSS)

---

### História 3.3 — Perguntas adaptativas
**Objetivo:** adaptar conversa com base no score.

#### Tarefas
- desenhar árvore de perguntas (arquivo JSON estático)
- implementar 2 a 4 perguntas adaptativas
- salvar respostas em estrutura de mensagens via fetch()
- permitir encerramento da conversa
- bolhas de chat com animação de entrada

#### Critério de aceite
- fluxo muda conforme a nota
- respostas ficam persistidas
- experiência de chat fluida sem page reload

---

## Epic 4 — Camada de IA

### História 4.1 — Gateway de modelos (custo zero)
**Objetivo:** integrar Ollama local e Gemini Free Tier sem acoplamento.

#### Tarefas
- criar serviço llm_client.py
- integrar LiteLLM com Ollama (ollama_chat/{model})
- integrar LiteLLM com Gemini Free Tier (gemini/{model})
- criar llm_fallback.py com regras estáticas
- parametrizar provider/model via .env
- implementar fallback chain: Ollama → Gemini → Regras estáticas
- tratar timeout, erro e fallback graceful

#### Critério de aceite
- app consegue chamar Ollama local quando disponível
- fallback para Gemini quando Ollama indisponível
- fallback para regras estáticas quando ambos indisponíveis
- troca de provider não exige refatoração

---

### História 4.2 — Sumarização dos feedbacks
**Objetivo:** gerar resumo executivo da sessão.

#### Tarefas
- criar prompt de sumarização
- consolidar respostas por sessão
- gerar resumo geral
- gerar highlights positivos e negativos
- salvar resultado em analysis_runs

#### Critério de aceite
- admin consegue gerar resumo com um clique
- resumo fica salvo no banco

---

### História 4.3 — Classificação temática
**Objetivo:** agrupar feedback por temas.

#### Tarefas
- definir taxonomy inicial (clareza, tempo, aplicabilidade, profundidade, exemplos, interação, material)
- criar prompt para classificar respostas
- persistir temas por resposta
- permitir múltiplos temas por feedback

#### Critério de aceite
- respostas aparecem classificadas em temas

---

## Epic 5 — Dashboard admin

### História 5.1 — Painel de sessões
**Objetivo:** visualizar sessões cadastradas.

#### Tarefas
- listar sessões
- mostrar quantidade de respostas
- mostrar status da análise
- mostrar link público

#### Critério de aceite
- painel mostra sessões com métricas básicas

---

### História 5.2 — Painel analítico da sessão
**Objetivo:** visualizar insights.

#### Tarefas
- mostrar score médio
- mostrar distribuição de notas
- mostrar taxa de resposta
- mostrar temas mais frequentes
- mostrar principais elogios
- mostrar principais críticas
- mostrar resumo executivo

#### Critério de aceite
- admin entende o resultado da sessão sem abrir banco manualmente

---

## Epic 6 — Exportação

### História 6.1 — Export CSV
**Objetivo:** exportar dados crus.

#### Tarefas
- exportar respostas por sessão
- exportar análise resumida

#### Critério de aceite
- admin baixa CSV corretamente

---

### História 6.2 — Export PDF simples
**Objetivo:** gerar resumo compartilhável.

#### Tarefas
- criar template de relatório com FPDF2
- gerar PDF simples da sessão

#### Critério de aceite
- PDF abre corretamente com dados resumidos

---

## Epic 7 — Qualidade e operação local

### História 7.1 — Testes mínimos
**Objetivo:** garantir estabilidade básica.

#### Tarefas
- testar rota /health
- testar criação de sessão
- testar submissão de resposta
- testar geração de análise

#### Critério de aceite
- testes principais passam localmente

---

### História 7.2 — Scripts de execução
**Objetivo:** subir projeto facilmente.

#### Tarefas
- criar Makefile com todos os comandos
- script .sh para rodar backend
- script .sh para rodar Streamlit
- script .sh para iniciar banco/migrações
- script .sh para configurar Ollama

#### Critério de aceite
- projeto sobe com comandos curtos (`make run`, `make db`, `make test`)

## 5. Estrutura de pastas

```text
agente-feedback-conversacional/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── sessions.py
│   │   │   ├── responses.py
│   │   │   ├── analysis.py
│   │   │   └── exports.py
│   │   ├── __init__.py
│   │   └── dependencies.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── participant.py
│   │   ├── response.py
│   │   ├── message.py
│   │   ├── theme.py
│   │   └── analysis_run.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   ├── participant.py
│   │   ├── response.py
│   │   ├── analysis.py
│   │   └── export.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session_service.py
│   │   ├── response_service.py
│   │   ├── conversation_service.py
│   │   ├── analysis_service.py
│   │   ├── theme_service.py
│   │   ├── export_service.py
│   │   ├── llm_client.py
│   │   └── llm_fallback.py
│   │
│   ├── prompts/
│   │   ├── summarize_session.md
│   │   ├── classify_feedback.md
│   │   └── adaptive_questions.md
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── participant_chat.html
│   │   └── thank_you.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── chat.css
│   │   └── js/
│   │       └── chat.js
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── scoring.py
│   │   ├── text.py
│   │   └── datetime.py
│   │
│   └── main.py
│
├── streamlit_app/
│   ├── Home.py
│   ├── pages/
│   │   ├── 1_Sessions.py
│   │   ├── 2_Session_Detail.py
│   │   └── 3_Exports.py
│   └── components/
│       └── __init__.py
│
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_sessions.py
│   ├── test_responses.py
│   └── test_analysis.py
│
├── scripts/
│   ├── run_api.sh
│   ├── run_streamlit.sh
│   ├── init_db.sh
│   ├── setup_ollama.sh
│   └── seed_demo_data.py
│
├── data/
│   └── .gitkeep
│
├── .env.example
├── .gitignore
├── README.md
├── Makefile
├── pyproject.toml
└── alembic.ini
```

## 6. Lista de endpoints

## Health

### GET /health
Retorna status da aplicação.

**Response**
```json
{
  "status": "ok"
}
```

---

## Sessions

### POST /api/v1/sessions
Cria uma nova sessão.

**Body**
```json
{
  "title": "Treinamento de Liderança",
  "description": "Sessão sobre comunicação e feedback",
  "score_type": "nps",
  "is_anonymous": true,
  "max_followup_questions": 3
}
```

**Response**
```json
{
  "id": 1,
  "public_token": "abc123xyz",
  "public_url": "http://localhost:8000/f/abc123xyz"
}
```

### GET /api/v1/sessions
Lista sessões.

### GET /api/v1/sessions/{session_id}
Detalha sessão.

### PATCH /api/v1/sessions/{session_id}
Atualiza sessão.

### DELETE /api/v1/sessions/{session_id}
Arquiva ou remove sessão.

---

## Participant flow

### GET /f/{public_token}
Renderiza página pública da sessão (template Jinja2 + Vanilla JS).

### POST /api/v1/public/{public_token}/start
Inicia a resposta do participante.

**Body**
```json
{
  "participant_name": "Opcional",
  "participant_email": null,
  "anonymous": true
}
```

**Response**
```json
{
  "response_id": 10,
  "first_question": {
    "type": "score",
    "text": "De 0 a 10, quão útil foi esta apresentação para o seu trabalho?"
  }
}
```

### POST /api/v1/public/{public_token}/score
Salva score inicial.

**Body**
```json
{
  "response_id": 10,
  "score": 8
}
```

**Response**
```json
{
  "next_question": {
    "type": "text",
    "text": "Qual foi o principal motivo da sua nota?"
  }
}
```

### POST /api/v1/public/{public_token}/message
Salva resposta textual e retorna próxima pergunta adaptativa.

**Body**
```json
{
  "response_id": 10,
  "message": "O conteúdo foi útil, mas faltaram exemplos práticos."
}
```

**Response**
```json
{
  "next_question": {
    "type": "text",
    "text": "O que tornaria essa sessão mais aplicável no seu dia a dia?"
  },
  "conversation_finished": false
}
```

### POST /api/v1/public/{public_token}/finish
Finaliza a conversa.

**Body**
```json
{
  "response_id": 10
}
```

**Response**
```json
{
  "status": "completed"
}
```

---

## Analysis

### POST /api/v1/sessions/{session_id}/analyze
Executa análise da sessão.

**Body**
```json
{
  "provider": "ollama",
  "model": "llama3.1:8b"
}
```

### GET /api/v1/sessions/{session_id}/analysis
Retorna análise mais recente.

**Response**
```json
{
  "summary": "A sessão foi bem avaliada, com elogios à clareza e críticas à falta de exemplos práticos.",
  "top_positive_themes": ["clareza", "objetividade"],
  "top_negative_themes": ["poucos exemplos", "tempo curto"],
  "avg_score": 8.4,
  "response_count": 34
}
```

---

## Exports

### GET /api/v1/sessions/{session_id}/export/csv
Exporta respostas.

### GET /api/v1/sessions/{session_id}/export/pdf
Exporta relatório simples (gerado com FPDF2).

## 7. Modelo de banco

## Tabela: sessions
Armazena as sessões de apresentação/treinamento.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| title | string | título da sessão |
| description | text | descrição |
| score_type | string | nps, csat, usefulness |
| is_anonymous | boolean | aceita anonimato |
| max_followup_questions | integer | limite de perguntas adaptativas |
| public_token | string unique | token do link público |
| status | string | draft, active, closed |
| created_at | datetime | criação |
| updated_at | datetime | atualização |

## Tabela: participants
Armazena dados opcionais do respondente.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| session_id | FK | sessão |
| name | string nullable | nome |
| email | string nullable | email |
| anonymous | boolean | resposta anônima |
| created_at | datetime | criação |

## Tabela: responses
Armazena resposta principal por participante.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| session_id | FK | sessão |
| participant_id | FK | participante |
| score | integer | nota principal |
| status | string | started, completed |
| started_at | datetime | início |
| completed_at | datetime nullable | conclusão |

## Tabela: messages
Armazena mensagens da conversa.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| response_id | FK | resposta |
| sender | string | system ou participant |
| message_order | integer | ordem da conversa |
| message_text | text | conteúdo |
| message_type | string | question, answer |
| created_at | datetime | criação |

## Tabela: themes
Armazena classificação temática por resposta.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| response_id | FK | resposta |
| theme_name | string | tema |
| sentiment | string | positive, neutral, negative |
| confidence | float | confiança |
| created_at | datetime | criação |

## Tabela: analysis_runs
Armazena resultado da análise consolidada.

| Campo | Tipo | Descrição |
|---|---|---|
| id | integer PK | identificador |
| session_id | FK | sessão |
| provider | string | ollama, gemini, static |
| model | string | nome do modelo |
| summary | text | resumo executivo |
| positives | JSON | pontos positivos |
| negatives | JSON | pontos negativos |
| recommendations | JSON | sugestões |
| avg_score | float | média |
| response_count | integer | quantidade |
| created_at | datetime | criação |

## 8. Configuração .env

```env
# Aplicação
APP_ENV=local
APP_NAME=feedback-agent-mvp
API_HOST=127.0.0.1
API_PORT=8000
STREAMLIT_PORT=8501
DATABASE_URL=sqlite:///./data/feedback_agent.db

# LLM — Estratégia de custo zero
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.1:8b
FALLBACK_LLM_PROVIDER=gemini
FALLBACK_LLM_MODEL=gemini-2.5-flash-lite

# Ollama (local, gratuito)
OLLAMA_BASE_URL=http://localhost:11434

# Gemini Free Tier (opcional - criar key em https://aistudio.google.com/apikey)
GEMINI_API_KEY=

# Para futuro uso (quando quiser pagar)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

## 9. Regras de negócio iniciais

- toda sessão precisa de public_token único (gerado com secrets.token_urlsafe(8))
- uma resposta pertence a uma única sessão
- um participante pode ser anônimo
- análise só roda se houver pelo menos 3 respostas completas
- score_type inicial aceito: nps, csat, usefulness
- máximo de 4 perguntas adaptativas na v1
- perguntas devem ser curtas e objetivas
- a pergunta principal deve sempre vir antes da conversa aberta
- se nenhum LLM estiver disponível, o sistema funciona com regras estáticas

## 10. Prompts que precisam existir desde o início

### Prompt 1 — perguntas adaptativas
Objetivo: definir próxima pergunta conforme score e histórico curto.

### Prompt 2 — sumarização executiva
Objetivo: gerar resumo em linguagem clara para gestor/RH.

### Prompt 3 — classificação temática
Objetivo: classificar em temas como clareza, tempo, aplicabilidade, profundidade, exemplos, interação, material.

## 11. Estratégia de LLM — Fallback Chain

```
Requisição LLM
    │
    ▼
┌─────────────────┐
│ Ollama rodando?  │──Sim──▶ Usa Ollama local (Llama 3.1 8B / Qwen 2.5)
└─────────────────┘          │
    │ Não                    │ Erro/Timeout
    ▼                        ▼
┌─────────────────────┐
│ Gemini key existe?   │──Sim──▶ Usa Gemini Free Tier (gemini-2.5-flash-lite)
└─────────────────────┘          │
    │ Não                        │ Erro/Quota
    ▼                            ▼
┌─────────────────────────┐
│ Regras estáticas         │──▶ Perguntas pré-definidas + sumarização por keywords
│ (produto nunca quebra)   │
└─────────────────────────┘
```

## 12. Critério de pronto do MVP
O MVP estará pronto quando você conseguir:

1. criar uma sessão
2. abrir o link público
3. responder a conversa completa (interface de chat sem reload)
4. ver as respostas no banco/painel
5. gerar resumo automático com IA (Ollama ou Gemini ou regras estáticas)
6. visualizar principais temas
7. exportar um CSV
8. exportar um PDF

---

## 13. Guia de implementação passo a passo

> Cada passo deve ser concluído e testado antes de avançar para o próximo.
> O critério "Pronto quando" define quando é seguro prosseguir.

---

### PASSO 1 — Inicialização do projeto
**Objetivo:** Estrutura de pastas, dependências e configuração base.

**Ações:**
1. Criar a estrutura de pastas completa (seção 5)
2. Criar `pyproject.toml` com todas as dependências:
   - fastapi, uvicorn[standard], sqlalchemy, alembic, pydantic, pydantic-settings
   - litellm, httpx, pandas, python-dotenv
   - loguru, fpdf2
   - jinja2, python-multipart
   - pytest, pytest-asyncio, httpx (dev)
   - streamlit, plotly
3. Criar ambiente virtual: `python -m venv .venv`
4. Instalar dependências: `pip install -e ".[dev]"`
5. Criar `.env.example` com todas as variáveis (seção 8)
6. Copiar `.env.example` para `.env`
7. Criar `.gitignore` (venv, .env, __pycache__, data/*.db, .mypy_cache)
8. Criar `README.md` com instruções de setup

**Pronto quando:** `pip install` roda sem erro e a estrutura de pastas existe.

---

### PASSO 2 — App FastAPI mínima + Health Check
**Objetivo:** Backend respondendo requisições.

**Ações:**
1. Criar `app/core/config.py` — leitura de variáveis com pydantic-settings
2. Criar `app/core/logging.py` — configuração do loguru
3. Criar `app/main.py` — instância FastAPI com metadata
4. Criar `app/api/routes/health.py` — rota GET /health
5. Registrar router na app
6. Criar `scripts/run_api.sh` — script para rodar uvicorn
7. Criar `Makefile` com target `run-api`

**Pronto quando:** `curl http://localhost:8000/health` retorna `{"status": "ok"}`.

---

### PASSO 3 — Banco de dados + Models SQLAlchemy
**Objetivo:** SQLite configurado com todas as tabelas.

**Ações:**
1. Criar `app/core/database.py` — engine SQLite, SessionLocal, get_db
2. Criar `app/models/base.py` — Base declarativa do SQLAlchemy
3. Criar `app/models/session.py` — modelo Session
4. Criar `app/models/participant.py` — modelo Participant
5. Criar `app/models/response.py` — modelo Response
6. Criar `app/models/message.py` — modelo Message
7. Criar `app/models/theme.py` — modelo Theme
8. Criar `app/models/analysis_run.py` — modelo AnalysisRun
9. Criar `app/models/__init__.py` — importar todos os modelos
10. Configurar Alembic: `alembic init migrations`
11. Ajustar `alembic.ini` e `migrations/env.py` para usar config do app
12. Gerar migração inicial: `alembic revision --autogenerate -m "initial"`
13. Aplicar migração: `alembic upgrade head`
14. Adicionar target `db` no Makefile

**Pronto quando:** `data/feedback_agent.db` existe e contém as 6 tabelas.

---

### PASSO 4 — Schemas Pydantic + CRUD de sessões
**Objetivo:** API de sessões funcionando.

**Ações:**
1. Criar `app/schemas/session.py` — SessionCreate, SessionRead, SessionUpdate, SessionList
2. Criar `app/services/session_service.py` — create, get, list, update, delete
3. Implementar geração de `public_token` com `secrets.token_urlsafe(8)`
4. Criar `app/api/routes/sessions.py`:
   - POST /api/v1/sessions
   - GET /api/v1/sessions
   - GET /api/v1/sessions/{session_id}
   - PATCH /api/v1/sessions/{session_id}
   - DELETE /api/v1/sessions/{session_id}
5. Criar `app/api/dependencies.py` — dependency injection para db session
6. Registrar router na app

**Pronto quando:** É possível criar uma sessão via Swagger UI (http://localhost:8000/docs) e obter o link público.

---

### PASSO 5 — Template HTML da interface do participante
**Objetivo:** Página pública com interface de chat.

**Ações:**
1. Configurar Jinja2Templates e StaticFiles no FastAPI
2. Criar `app/templates/base.html` — layout base responsivo
3. Criar `app/templates/participant_chat.html` — interface de chat:
   - Área de mensagens (bolhas de chat)
   - Input de score (botões 0-10)
   - Input de texto (campo + botão enviar)
   - Animações CSS de entrada das bolhas
4. Criar `app/static/css/chat.css` — estilos da interface
5. Criar `app/static/js/chat.js` — lógica de interação:
   - Funções fetch() para cada endpoint (/start, /score, /message, /finish)
   - Renderização dinâmica de bolhas
   - Gerenciamento de estado da conversa
6. Criar `app/templates/thank_you.html` — tela de agradecimento
7. Criar rota GET /f/{public_token} que renderiza o template

**Pronto quando:** Acessar http://localhost:8000/f/{token} mostra interface de chat funcional (mesmo sem backend dos endpoints de resposta).

---

### PASSO 6 — Endpoints do fluxo público do participante
**Objetivo:** Conversa completa funciona de ponta a ponta.

**Ações:**
1. Criar `app/schemas/participant.py` — ParticipantCreate
2. Criar `app/schemas/response.py` — ResponseStart, ScoreSubmit, MessageSubmit
3. Criar `app/services/response_service.py` — lógica de criação e atualização
4. Criar `app/services/conversation_service.py` — lógica de perguntas adaptativas
5. Criar `app/api/routes/responses.py`:
   - POST /api/v1/public/{public_token}/start
   - POST /api/v1/public/{public_token}/score
   - POST /api/v1/public/{public_token}/message
   - POST /api/v1/public/{public_token}/finish
6. Persistir cada mensagem (pergunta e resposta) na tabela messages
7. Registrar router na app

**Pronto quando:** Um usuário consegue fazer a conversa inteira pelo browser e os dados aparecem no banco.

---

### PASSO 7 — Regras de perguntas adaptativas
**Objetivo:** Perguntas mudam conforme a nota.

**Ações:**
1. Criar arquivo `app/prompts/adaptive_questions.md` com árvore de perguntas
2. Criar arquivo JSON/YAML com perguntas categorizadas por faixa de score:
   - Score 0-6 (detratores): foco em frustração, lacunas
   - Score 7-8 (neutros): foco em melhorias possíveis
   - Score 9-10 (promotores): foco em valor, recomendação
3. Atualizar `conversation_service.py` para selecionar perguntas por faixa
4. Implementar limite de máximo 4 perguntas por conversa
5. Salvar cada pergunta emitida pelo sistema na tabela messages

**Pronto quando:** Ao dar nota 3, as perguntas exploram frustração. Ao dar nota 9, exploram valor.

---

### PASSO 8 — Painel admin básico (Streamlit)
**Objetivo:** Admin consegue ver sessões e métricas.

**Ações:**
1. Criar `streamlit_app/Home.py` — página inicial com visão geral
2. Criar `streamlit_app/pages/1_Sessions.py`:
   - Botão de criar nova sessão (chama API via httpx)
   - Lista de sessões com total de respostas, score médio, status
   - Link público copiável
3. Criar `streamlit_app/pages/2_Session_Detail.py`:
   - Detalhes da sessão selecionada
   - Lista de respostas recebidas
   - Score médio, distribuição
4. Criar `scripts/run_streamlit.sh`
5. Adicionar target `run-streamlit` no Makefile

**Pronto quando:** `make run-streamlit` abre painel com sessões listadas e métricas básicas.

---

### PASSO 9 — Integração com LLM (Ollama + Gemini + Fallback)
**Objetivo:** Sistema consegue chamar LLM com custo zero.

**Ações:**
1. Criar `app/services/llm_client.py`:
   - Função `call_llm(prompt, system_prompt)` que usa LiteLLM
   - Tenta Ollama primeiro (ollama_chat/{model})
   - Se falhar, tenta Gemini (gemini/{model})
   - Se falhar, retorna None (para fallback estático)
   - Logging de cada tentativa e fallback
2. Criar `app/services/llm_fallback.py`:
   - Sumarização por contagem/keywords quando LLM indisponível
   - Classificação por matching de palavras-chave em temas fixos
3. Criar `scripts/setup_ollama.sh`:
   - Verificar se Ollama está instalado
   - Baixar modelo recomendado
4. Testar com Ollama local (se disponível)
5. Testar sem Ollama (verificar fallback funciona)

**Pronto quando:** `llm_client.call_llm("Resuma em 1 frase: feedback positivo sobre clareza")` retorna resposta (de Ollama, Gemini ou fallback).

---

### PASSO 10 — Sumarização e classificação temática
**Objetivo:** Gerar insights consolidados da sessão.

**Ações:**
1. Criar `app/prompts/summarize_session.md` — prompt de resumo executivo
2. Criar `app/prompts/classify_feedback.md` — prompt de classificação
3. Criar `app/services/analysis_service.py`:
   - Consolidar todas as respostas textuais da sessão
   - Chamar LLM para gerar resumo (positivos, negativos, recomendações)
   - Chamar LLM para classificar cada resposta em temas
   - Se LLM indisponível, usar llm_fallback.py
   - Salvar resultados em analysis_runs e themes
4. Criar `app/schemas/analysis.py` — AnalysisRequest, AnalysisResponse
5. Criar `app/api/routes/analysis.py`:
   - POST /api/v1/sessions/{session_id}/analyze
   - GET /api/v1/sessions/{session_id}/analysis
6. Registrar router na app

**Pronto quando:** POST /analyze gera resumo e temas. GET /analysis retorna dados consolidados.

---

### PASSO 11 — Dashboard analítico completo
**Objetivo:** Painel admin com todos os insights visuais.

**Ações:**
1. Atualizar `streamlit_app/pages/2_Session_Detail.py`:
   - Gráfico de distribuição de notas (bar chart)
   - Top temas positivos e negativos (bar chart horizontal)
   - Resumo executivo (text block)
   - Lista de comentários recentes
   - Taxa de concluídos vs iniciados (pie chart)
   - Botão "Gerar Análise" que chama POST /analyze
2. Usar Plotly para gráficos interativos

**Pronto quando:** Painel mostra todos os gráficos e insights. Serve para demo.

---

### PASSO 12 — Exportação CSV e PDF
**Objetivo:** Dados compartilháveis.

**Ações:**
1. Criar `app/services/export_service.py`:
   - Gerar CSV de respostas (pandas DataFrame → CSV)
   - Gerar CSV de temas
   - Gerar PDF do resumo da sessão (FPDF2)
2. Criar `app/schemas/export.py`
3. Criar `app/api/routes/exports.py`:
   - GET /api/v1/sessions/{session_id}/export/csv
   - GET /api/v1/sessions/{session_id}/export/pdf
4. Registrar router na app
5. Adicionar botões de export no Streamlit (Session Detail)

**Pronto quando:** Download de CSV e PDF funciona pelo Swagger e pelo Streamlit.

---

### PASSO 13 — Testes mínimos
**Objetivo:** Cobertura básica do fluxo principal.

**Ações:**
1. Criar `tests/conftest.py` — fixtures de banco de teste e client AsyncIO
2. Criar `tests/test_health.py` — testar GET /health
3. Criar `tests/test_sessions.py` — testar CRUD de sessões
4. Criar `tests/test_responses.py` — testar fluxo completo de resposta
5. Criar `tests/test_analysis.py` — testar geração de análise
6. Adicionar target `test` no Makefile

**Pronto quando:** `make test` passa com todos os testes verdes.

---

### PASSO 14 — Scripts finais e documentação
**Objetivo:** Projeto pronto para demo.

**Ações:**
1. Criar `scripts/seed_demo_data.py` — dados de exemplo para demo
2. Finalizar Makefile com todos os targets:
   - `make setup` — criar venv + instalar deps
   - `make db` — rodar migrações
   - `make run-api` — subir backend
   - `make run-streamlit` — subir painel
   - `make run` — subir tudo
   - `make test` — rodar testes
   - `make seed` — popular com dados demo
   - `make clean` — limpar banco e cache
3. Atualizar `README.md` com:
   - Descrição do projeto
   - Requisitos (Python 3.11+, opcional: Ollama)
   - Instruções de instalação e execução
   - Screenshots/descrição do fluxo
   - Configuração de LLM (Ollama / Gemini / sem LLM)
4. Fazer git add, commit e push final

**Pronto quando:** Qualquer pessoa consegue clonar, instalar e rodar o MVP completo seguindo o README.

---

### PASSO 15 — Validação completa do MVP
**Objetivo:** Verificar todos os critérios de aceite do MVP (seção 12).

**Checklist final:**
1. [ ] Criar uma sessão pelo painel admin
2. [ ] Abrir o link público no browser
3. [ ] Responder a conversa completa (chat sem reload)
4. [ ] Verificar dados no banco/painel
5. [ ] Gerar resumo automático com IA
6. [ ] Visualizar temas classificados
7. [ ] Exportar CSV
8. [ ] Exportar PDF
9. [ ] Todos os testes passando
10. [ ] README claro e completo

**Pronto quando:** Todos os 10 itens acima estão marcados. MVP completo.
