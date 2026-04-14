# Privacidade, Retencao e LGPD Minima

Este documento define o minimo operacional de privacidade para a instancia atual do produto.

## 1. Escopo dos dados

O produto pode armazenar:

- identificacao opcional do participante: nome e email, quando informados
- respostas, notas e mensagens trocadas na conversa
- analises consolidadas por sessao
- exportacoes operacionais em CSV e PDF
- logs tecnicos e de auditoria

## 2. Regra atual de identificacao

- o nome do participante e opcional
- se o campo nao for preenchido, o participante aparece como `Anonimo`
- a anonimidade remove nome e email, mas nao impede o uso da resposta para analise agregada da sessao

## 3. Regra atual de consentimento

Antes de iniciar a conversa publica, o participante precisa marcar que concorda em compartilhar as respostas para analise da sessao.

O texto publico deixa claro que:

- as respostas serao usadas para consolidar aprendizados e melhorar a experiencia
- a organizacao define a base legal operacional do tratamento
- provedores de IA configurados pela organizacao podem ser usados para perguntas e analises

## 4. Politica minima de retencao

Padrao atual da aplicacao:

- respostas: ate 365 dias
- analises: ate 365 dias
- logs operacionais: ate 30 dias
- exportacoes: ate 30 dias

Observacoes:

- PDFs gerados pela aplicacao mantem somente os 2 arquivos mais recentes por sessao
- excluir uma sessao remove respostas, participantes, analises e exportacoes associadas

## 5. Atendimento minimo de LGPD na operacao

Hoje a operacao consegue responder o basico com estes mecanismos:

- exclusao completa por sessao: remove todos os dados ligados a sessao
- exportacao por participante: retorna identificacao, respostas e mensagens associadas
- anonimização por participante: remove nome e email, preservando o conteudo para leitura agregada

## 6. Responsabilidades sobre IA

- a organizacao operadora define se usa credenciais proprias ou credenciais da plataforma
- dados enviados a provedores de IA seguem a configuracao ativa da instancia
- a organizacao deve informar a base legal e revisar o uso de provedores externos antes de uso com cliente final

## 7. Limites desta etapa

Esta sprint entrega LGPD minima para MVP comercial responsavel, mas ainda nao substitui:

- politica juridica formal
- DPA com clientes e provedores
- automacao completa de limpeza por janela temporal
- governanca corporativa completa de consentimento por tenant
