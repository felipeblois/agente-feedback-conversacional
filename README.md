# InsightFlow - MVP

InsightFlow e uma plataforma de feedback conversacional para treinamentos, palestras, workshops, onboardings e encontros internos. O produto combina coleta guiada por IA, leitura qualitativa estruturada e visao executiva para transformar feedback em decisao operacional.

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
- API key da OpenAI ou Anthropic para fallback cloud
- credenciais do admin da instancia no `.env`

## Setup rapido

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional
make setup
scripts/doctor.sh
```

## Ambientes

Use configuracoes separadas para local e EC2.

No uso local com WSL, o `.env` deve apontar para `localhost`:

```env
APP_ENV=local
INSTANCE_NAME=local-instance
INSTANCE_ID=local-default
API_BASE_URL=http://localhost:8000
ADMIN_BASE_URL=http://localhost:8501
PUBLIC_BASE_URL=http://localhost:8000
CORS_ALLOWED_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

Para EC2, use um arquivo de referencia separado como `deploy/env/.env.ec2.example` e depois copie os valores corretos para o `.env` da instancia.

## Demo em 5 minutos

1. Suba a stack com `scripts/start.sh`
2. Acesse o painel admin em `http://localhost:8501`
3. Entre com o bootstrap definido no `.env`
4. Crie uma sessao com briefing estruturado
5. Abra o link publico da sessao e simule 1 ou 2 respostas
6. Volte ao painel da sessao e gere a analise executiva
7. Use o dashboard para contar a narrativa: criacao, coleta, insight, comparativo e exportacao gerencial

## Protecao do admin

O painel admin e os endpoints administrativos exigem autenticacao.

Variaveis recomendadas no `.env`:
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_API_TOKEN` opcional
- `INSTANCE_NAME`
- `INSTANCE_ID`
- `RETENTION_RESPONSES_DAYS`
- `RETENTION_ANALYSES_DAYS`
- `RETENTION_LOGS_DAYS`
- `RETENTION_EXPORTS_DAYS`
- `PRIVACY_CONTACT_EMAIL`

Se `ADMIN_API_TOKEN` ficar vazio, a aplicacao gera internamente um token administrativo a partir da configuracao da instancia.

Bootstrap atual:
- `ADMIN_USERNAME` e `ADMIN_PASSWORD` continuam sendo a credencial inicial da instancia
- com esse bootstrap, o primeiro admin pode entrar no painel e cadastrar usuarios admin nominais
- depois disso, o login pode ser feito tanto pelo bootstrap quanto pelos admins salvos no banco

Antes de uso real com cliente:
- troque a senha padrao `change-me-admin`
- defina `INSTANCE_NAME` e `INSTANCE_ID` por instancia
- revise as chaves Gemini, OpenAI e Claude da instancia
- crie usuarios admin nominais para rastrear quem cria e opera sessoes

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

# backup
scripts/backup.sh manual

# validar backup
scripts/backup_verify.sh data/backups/insightflow_backup_<timestamp>_manual.tar.gz
```

## Fluxo de uso

### Criar uma sessao
Use o painel admin em `http://localhost:8501` para abrir uma nova rodada de feedback com:
- titulo e descricao
- tipo de feedback
- briefing estruturado para a IA
- limite de perguntas de aprofundamento

### Coletar feedbacks
Compartilhe o link publico `http://localhost:8000/f/{token}` com os participantes para iniciar a conversa guiada.

### Visualizar resultados
Acesse o painel admin em `http://localhost:8501` para acompanhar operacao, leitura executiva, historico e comparativos entre sessoes.

### Operar sessoes no admin
No painel Streamlit agora e possivel:
- criar sessoes com briefing estruturado para IA
- editar titulo, descricao, briefing e limite de aprofundamento
- arquivar sessoes ativas
- reativar sessoes arquivadas
- acompanhar detalhe, respostas recentes e exportacoes
- administrar usuarios nominais do painel
- desativar, trocar senha e excluir admins nominais com auditoria minima

### Privacidade e LGPD minima
O produto agora inclui uma base minima de privacidade para operacao responsavel:
- consentimento explicito antes de iniciar a conversa publica
- exportacao de dados por participante
- anonimizacao de participante preservando leitura agregada
- politica operacional de retencao configuravel via `.env`

### Configurar credenciais da instancia
Use a pagina `Configuracoes` no painel para definir se a instancia usa:
- credenciais do cliente
- credenciais da plataforma

O runtime pode operar com `Gemini`, `OpenAI` e `Claude`, com `Jarvis` como fallback estatico.
As alteracoes de settings registram uma trilha minima de auditoria no backend.

O painel de configuracoes aceita:
- `Gemini`
- `OpenAI`
- `Claude`

para motor principal e fallback, conforme a estrategia da instancia.

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
| `scripts/backup.sh` | Gera backup da instancia com `.env`, banco SQLite e exportacoes |
| `scripts/restore.sh` | Restaura um backup no ambiente atual ou em diretorio de teste |
| `scripts/backup_verify.sh` | Valida um backup via restore temporario |

## Roteiro recomendado para piloto

1. Ajuste `INSTANCE_NAME`, `INSTANCE_ID`, `ADMIN_USERNAME` e `ADMIN_PASSWORD`
2. Valide o ambiente com `scripts/doctor.sh`
3. Cadastre ao menos um admin nominal para rastrear autoria das sessoes
4. Gere uma sessao de demonstracao com briefing claro, objetivo e orientado a negocio
5. Simule respostas reais pelo link publico antes da apresentacao
6. Valide a analise e as exportacoes antes da conversa com cliente
7. Use o dashboard como tela de abertura, o detalhe da sessao como tela principal de valor e a exportacao como fechamento comercial

## Estrategia de LLM

O painel pode operar com:

1. Gemini
2. OpenAI
3. Claude

em qualquer combinacao entre motor principal e fallback cloud.

Se os provedores cloud falharem, o sistema continua respondendo com a analise estatica local Jarvis.

## Modelo comercial

- Instancia dedicada por cliente
- O cliente pode salvar suas proprias credenciais no painel
- A plataforma pode operar com chaves da propria operacao quando isso fizer sentido comercial
- O fallback estatico Jarvis continua disponivel como failsafe
- Auditoria minima, exportacoes e leitura executiva apoiam demos, pilotos e venda assistida

## Documentacao complementar

- `USER_MANUAL.md`: operacao do painel, do fluxo participante e leitura executiva
- `DEMO_PLAYBOOK.md`: roteiro curto para demos, pilotos e venda assistida
- `PRIVACY_AND_RETENTION.md`: regras minimas de privacidade, retencao e LGPD operacional
- `BACKUP_AND_RESTORE.md`: rotina de backup, restore e contingencia

## Stack

- Backend: FastAPI + SQLAlchemy + Alembic + SQLite
- Frontend participante: HTML/CSS/JS
- Dashboard admin: Streamlit
- IA: LiteLLM com Gemini, OpenAI e Anthropic
- PDF: FPDF2
