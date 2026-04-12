# Manual de Utilizacao - Agente de Feedback Conversacional

Este manual detalha como operar o painel administrativo em Streamlit e como funciona o fluxo do participante no MVP do Agente de Feedback.

## 1. Visao geral da arquitetura

O ecossistema e dividido em tres partes:
1. Backend FastAPI na porta `8000`
2. Sistema publico de chat para o participante
3. Dashboard admin em Streamlit na porta `8501`

## 2. Painel do administrador

### Dashboard e sessoes
- Crie novas sessoes com titulo, descricao e tipo de nota
- Compartilhe o link publico `http://localhost:8000/f/{token}`
- Acompanhe respostas, conclusao e analises no dashboard

### Configuracoes
- Escolha entre credenciais do cliente e credenciais da plataforma
- Salve Gemini e Anthropic por instancia
- Teste a conectividade antes de operar a analise

### Detalhe da sessao
- Gere a analise com IA
- Veja resumo executivo, temas, elogios, criticas e recomendacoes
- Exporte CSV e PDF quando houver material disponivel

## 3. Fluxo do participante

1. O participante acessa o link publico
2. Pode informar o nome opcionalmente
3. Responde a nota principal
4. Continua o chat com perguntas de aprofundamento
5. Recebe a mensagem final de encerramento

## 4. Estrategia de inteligencia artificial

O projeto usa uma cascata simples e comercializavel:

1. Gemini como provedor principal
2. Anthropic como fallback cloud
3. Fallback estatico como failsafe final

Se os dois provedores cloud falharem, o sistema continua gerando uma analise simplificada local para nao quebrar a operacao.
