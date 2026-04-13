# Demo Playbook

Guia curto para demonstracoes previsiveis do Agente de Feedback Conversacional.

## Antes da demo

1. Rode `scripts/doctor.sh`
2. Suba a stack com `scripts/start.sh`
3. Confirme `http://localhost:8000/health`
4. Confirme `http://localhost:8501`
5. Garanta uma sessao pronta com link publico valido
6. Se possivel, deixe 1 ou 2 respostas seedadas para nao depender da internet ou de improviso

## Sequencia recomendada

1. Abra o dashboard e contextualize valor do produto
2. Mostre a tela de criacao de sessao com briefing estruturado
3. Explique o controle de aprofundamento da IA
4. Abra o link publico e percorra o fluxo do participante
5. Volte ao detalhe da sessao e gere a analise
6. Mostre resumo executivo, temas e recomendacoes
7. Finalize com exportacoes e sessoes arquivadas

## Mensagem comercial sugerida

- O admin cria a sessao sem depender de formulario fixo
- A IA conduz o aprofundamento com base no briefing do contexto
- O time responsavel recebe leitura executiva e historico operacional
- A instancia pode operar com credenciais do cliente ou da plataforma

## Se algo falhar durante a demo

1. Verifique `scripts/status.sh`
2. Use uma sessao ja pronta
3. Se o provedor cloud falhar, explique o fallback Jarvis como failsafe operacional
4. Priorize mostrar o valor do fluxo completo: criacao, coleta, insight e exportacao
