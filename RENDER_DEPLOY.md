# Deploy no Render

Guia rapido para publicar a primeira versao online usando Render.

## O que ja foi preparado

- blueprint `render.yaml`
- suporte a Postgres via `DATABASE_URL`
- `API_BASE_URL`, `PUBLIC_BASE_URL` e `ADMIN_BASE_URL`
- links publicos da sessao sem `localhost`
- CORS configuravel para API e admin separados

## Arquitetura prevista

- `feedback-agent-api`: FastAPI
- `feedback-agent-admin`: Streamlit
- `feedback-agent-db`: Postgres

## Como subir

1. Faça push do repositório atualizado
2. No Render, escolha `New +` -> `Blueprint`
3. Aponte para este repositório
4. Revise o `render.yaml`
5. Confirme a criação dos 3 recursos

## Variáveis sensíveis que você vai preencher no Render

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_API_TOKEN` opcional
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

## URLs importantes

Depois do deploy, valide:

- API: `https://feedback-agent-api.onrender.com/health`
- Admin: `https://feedback-agent-admin.onrender.com`

Se o Render gerar slugs diferentes, ajuste estas variáveis:

- `API_BASE_URL`
- `PUBLIC_BASE_URL`
- `ADMIN_BASE_URL`
- `CORS_ALLOWED_ORIGINS`

## Comportamento esperado no free tier

- o serviço pode entrar em sleep por inatividade
- a primeira resposta pode demorar mais por cold start
- esta configuracao serve melhor para demo, homologacao e primeiros testes externos

## Checklist depois do deploy

1. `health` da API responde `ok`
2. o admin abre no navegador
3. o login bootstrap funciona
4. a criacao de sessao gera link publico valido
5. o fluxo do participante abre pela web
6. a analise executa com as chaves configuradas
