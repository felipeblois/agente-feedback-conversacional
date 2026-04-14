# Agente de Feedback Conversacional - MVP

Agente de feedback conversacional pos-apresentacao, treinamento e eventos internos. Coleta notas e respostas guiadas por IA, consolida sinais qualitativos e entrega leitura executiva para o time responsavel.

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

## Deploy no Render

O projeto agora ja vem preparado para uma primeira hospedagem no Render com:
- `render.yaml` para API, admin e banco
- suporte a `DATABASE_URL` em Postgres
- URLs publicas configuraveis por ambiente
- CORS e links publicos sem dependencia de `localhost`

Variaveis principais para cloud:
- `DATABASE_URL`
- `API_BASE_URL`
- `PUBLIC_BASE_URL`
- `ADMIN_BASE_URL`
- `CORS_ALLOWED_ORIGINS`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Fluxo recomendado no Render:

1. Conecte o repositorio ao Render
2. Crie os servicos usando o `render.yaml`
3. Revise os nomes publicos gerados e ajuste as URLs caso o slug final mude
4. Preencha as variaveis sensiveis marcadas com `sync: false`
5. Aguarde o deploy da API e do admin
6. Valide `https://<api>/health`
7. Acesse `https://<admin>` e entre com o bootstrap

Observacao:
- o plano free do Render pode dormir por inatividade
- a primeira versao para cloud foi preparada para demo, homologacao e validacao externa
- para operacao mais estavel no futuro, a migracao para plano pago ou outra infra continua recomendada

## Demo em 5 minutos

1. Suba a stack com `scripts/start.sh`
2. Acesse o painel admin em `http://localhost:8501`
3. Entre com o bootstrap definido no `.env`
4. Crie uma sessao com briefing estruturado
5. Abra o link publico da sessao e simule 1 ou 2 respostas
6. Volte ao detalhe da sessao e gere a analise
7. Use o dashboard para contar a narrativa: criacao, coleta, insight e exportacao

## Protecao do admin

O painel admin e os endpoints administrativos agora exigem autenticacao.

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
- revise as chaves Gemini e Anthropic da instancia
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
Use o painel admin em `http://localhost:8501` para criar sessoes com:
- titulo e descricao
- tipo de feedback
- briefing estruturado para a IA
- limite de perguntas de aprofundamento

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
- administrar usuarios nominais do painel
- desativar, trocar senha e excluir admins nominais com auditoria minima

### Privacidade e LGPD minima
O produto agora inclui uma base minima de privacidade para operacao:
- consentimento explicito antes de iniciar a conversa publica
- exportacao de dados por participante
- anonimização de participante preservando leitura agregada
- politica operacional de retencao configuravel via `.env`

### Configurar credenciais da instancia
Use a pagina `Configuracoes` no painel para definir se a instancia usa:
- credenciais do cliente
- credenciais da plataforma

O runtime segue a ordem `Gemini -> Anthropic -> Jarvis`.
As alteracoes de settings passam a registrar uma trilha minima de auditoria no backend.

O painel de configuracoes agora aceita:
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
| `scripts/restore.sh` | Restaura um backup no ambiente atual ou em diretório de teste |
| `scripts/backup_verify.sh` | Valida um backup via restore temporario |

## Roteiro recomendado para piloto

1. Ajuste `INSTANCE_NAME`, `INSTANCE_ID`, `ADMIN_USERNAME` e `ADMIN_PASSWORD`
2. Valide o ambiente com `scripts/doctor.sh`
3. Cadastre ao menos um admin nominal para rastrear autoria das sessoes
4. Gere uma sessao de demonstração com briefing claro e objetivo
5. Simule respostas reais pelo link publico antes da apresentacao
6. Valide a analise e as exportacoes antes da conversa com cliente
7. Use o dashboard como tela de abertura e o detalhe da sessao como tela principal de valor

## Estrategia de LLM

O painel agora pode operar com:

1. Gemini
2. OpenAI
3. Claude

em qualquer combinacao entre motor principal e fallback cloud.

Se os provedores cloud falharem, o sistema continua respondendo com a analise estatica local.

## Modelo comercial

- Instancia dedicada por cliente
- O cliente pode salvar suas proprias credenciais no painel
- Se preferir, a instancia pode usar as credenciais da plataforma
- O fallback estatico Jarvis continua disponivel como failsafe

## Documentacao complementar

- `USER_MANUAL.md`: operacao do painel e do fluxo participante
- `DEMO_PLAYBOOK.md`: roteiro curto para demos e pilotos assistidos
- `PRIVACY_AND_RETENTION.md`: regras minimas de privacidade, retencao e LGPD operacional
- `BACKUP_AND_RESTORE.md`: rotina de backup, restore e contingencia

## Stack

- Backend: FastAPI + SQLAlchemy + Alembic + SQLite
- Frontend participante: HTML/CSS/JS
- Dashboard admin: Streamlit
- IA: LiteLLM com Gemini e Anthropic
- PDF: FPDF2
