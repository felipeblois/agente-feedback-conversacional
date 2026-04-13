# Manual de Utilizacao - Agente de Feedback Conversacional

Este manual foi pensado para operacao local, demos assistidas e pilotos com cliente. O foco e ajudar o admin a instalar, subir a stack e conduzir o fluxo completo sem ruido.

## 1. Portas e componentes

- Backend FastAPI: `http://localhost:8000`
- Painel admin em Streamlit: `http://localhost:8501`
- Link publico do participante: `http://localhost:8000/f/{token}`

## 2. Preparacao inicial

Antes da primeira execucao:

1. Ajuste o `.env` com as credenciais da instancia
2. Defina pelo menos `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `INSTANCE_NAME` e `INSTANCE_ID`
3. Salve a chave Gemini e, se desejado, a chave Anthropic
4. Rode `make setup`
5. Rode `scripts/doctor.sh`

## 3. Subida e operacao local

Fluxo recomendado no WSL:

```bash
cd /mnt/c/Users/felip/Documents/projeto_1/agente-feedback-conversacional
scripts/start.sh
scripts/status.sh
```

Para encerrar:

```bash
scripts/stop_all.sh
```

## 4. Primeiro acesso ao painel

1. Abra `http://localhost:8501`
2. Entre com o bootstrap configurado no `.env`
3. Acesse `Configuracoes`
4. Cadastre admins nominais para rastrear quem opera a instancia

O bootstrap deve ser tratado como acesso inicial e contingencia. Para uso real, prefira admins nominais.

## 5. Criar uma sessao de feedback

Na tela `Sessoes`, o admin pode:

- definir titulo e descricao
- escolher o tipo de feedback
- preencher o briefing estruturado
- informar tema principal, objetivo, publico e topicos
- ajustar o limite de aprofundamento da IA

O limite de aprofundamento controla quantas perguntas abertas a IA pode fazer ao participante.

## 6. Fluxo do participante

1. O participante acessa o link publico da sessao
2. Pode informar o nome ou seguir como anonimo
3. Responde a nota principal
4. A IA conduz perguntas de aprofundamento de acordo com o briefing
5. O fluxo termina com a tela de agradecimento

## 7. Operacao do detalhe da sessao

Na tela `Detalhe da sessao`, o admin consegue:

- acompanhar respostas e taxa de conclusao
- ver distribuicao de notas
- revisar respostas recentes
- gerar analise com IA
- exportar CSV e PDF
- editar briefing e configuracoes da sessao
- arquivar ou excluir a sessao

## 8. Sessoes arquivadas

As sessoes arquivadas vao para a area `Sessoes arquivadas`, onde o time pode:

- consultar o historico
- revisar insights
- reativar a sessao se necessario

## 9. Administracao de usuarios

Na tela `Configuracoes`, o admin pode:

- criar admin nominal
- desativar ou reativar usuarios
- trocar senha
- excluir admin nominal

Protecoes importantes:

- o usuario conectado nao pode se autoexcluir
- a autoria das sessoes continua preservada mesmo se um admin nominal for excluido
- alteracoes sensiveis entram na auditoria minima do sistema

## 10. Motores de analise

O runtime atual segue esta ordem:

1. Gemini
2. Anthropic
3. Jarvis como fallback estatico

Se os provedores cloud falharem, o sistema tenta preservar a experiencia com o fallback local.

## 11. Roteiro de demo sugerido

1. Abra o dashboard para contextualizar o produto
2. Mostre a criacao de uma sessao com briefing estruturado
3. Abra o link publico e simule uma resposta
4. Volte ao detalhe e gere a analise
5. Encerre mostrando resumo executivo, temas e exportacoes

## 12. Checklist de estabilidade antes de apresentar

- `scripts/doctor.sh` executado sem erro
- API respondendo em `http://localhost:8000/health`
- painel abrindo em `http://localhost:8501`
- pelo menos uma sessao pronta para demo
- analise e exportacoes validadas antes da reuniao
