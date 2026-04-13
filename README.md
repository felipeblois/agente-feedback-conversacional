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
- API key do Gemini
- API key da Anthropic para fallback cloud

## Setup rapido

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional
make setup
scripts/doctor.sh
```

## Operacao diaria

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional

# diagnostico do ambiente
scripts/doctor.sh

# iniciar stack completa
scripts/start.sh

# ver status
scripts/status.sh

# parar stack
scripts/stop_all.sh

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

### Operar sessoes no admin
No painel Streamlit agora e possivel:
- criar sessoes com briefing estruturado para IA
- editar titulo, descricao, briefing e limite de aprofundamento
- arquivar sessoes ativas
- reativar sessoes arquivadas
- acompanhar detalhe, respostas recentes e exportacoes

### Configurar credenciais da instancia
Use a pagina `Configuracoes` no painel para definir se a instancia usa:
- credenciais do cliente
- credenciais da plataforma

O runtime segue a ordem `Gemini -> Anthropic -> Jarvis`.

## Comandos disponiveis

| Comando | Descricao |
|---|---|
| `make setup` | Cria venv, instala dependencias e aplica migrations |
| `make db` | Inicializa ou atualiza o banco |
| `make run-api` | Sobe o backend FastAPI |
| `make run-streamlit` | Sobe o painel admin |
| `make run` | Sobe backend e admin em background |
| `make test` | Roda os testes |
| `make seed` | Popula com dados de exemplo |
| `scripts/doctor.sh` | Valida o ambiente WSL e a venv |
| `scripts/start.sh` | Atalho para subir a stack completa |
| `scripts/run_all.sh` | Aplica migrations e sobe API + Streamlit no mesmo terminal |
| `scripts/status.sh` | Mostra status da stack e portas em uso |
| `scripts/stop_all.sh` | Finaliza API e Streamlit da stack local |
| `scripts/test.sh` | Executa os testes pela venv Linux |

## Estrategia de LLM

1. Gemini como provedor principal
2. Anthropic como fallback cloud
3. Regras estaticas como failsafe final

Se os dois provedores cloud falharem, o sistema continua respondendo com a analise estatica local.

## Modelo comercial

- Instancia dedicada por cliente
- O cliente pode salvar suas proprias credenciais no painel
- Se preferir, a instancia pode usar as credenciais da plataforma
- O fallback estatico Jarvis continua disponivel como failsafe

## Stack

- Backend: FastAPI + SQLAlchemy + Alembic + SQLite
- Frontend participante: HTML/CSS/JS
- Dashboard admin: Streamlit
- IA: LiteLLM com Gemini e Anthropic
- PDF: FPDF2
