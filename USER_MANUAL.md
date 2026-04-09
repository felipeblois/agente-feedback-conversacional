# Manual de Utilização — Agente de Feedback Conversacional

Este manual detalha como operar o **Painel Administrativo (Streamlit)** e como funciona o fluxo do **Participante** no MVP do Agente de Feedback. A solução foi projetada para ser simples, local e sem custos imediatos com APIs de IA.

---

## 🏗️ 1. Visão Geral da Arquitetura

O ecossistema é dividido em três grandes partes:
1. **O Backend (API REST)**: Processa as requisições, orquestra o LLM (inteligência artificial) e interage com o banco de dados. Roda na porta `8000`.
2. **Sistema Público de Chat (Para o Participante)**: Onde o público-alvo acessa o link, envia suas notas e conversa com o assistente inteligente.
3. **Dashboard Admin (Streamlit)**: Onde você (criador) entra para gerenciar as sessões, observar as estatísticas consolidadas por IA e exportar relatórios. Roda na porta `8501`.

---

## 👨‍💼 2. Painel do Administrador (Gestão de Resultados)

O fluxo principal e estratégico de operação de eventos acontece através do seu painel do Administrador local.  Quando inicializado (`make run`), acesse `http://localhost:8501` no seu navegador.

### Visão Inicial (`1_Sessions`)
> **Objetivo:** Criar e gerenciar "Salas" ou "Sessões" de coleta de feedbacks.

- **Nova Sessão:** Você define um nome (ex: "Treinamento Anual Vendas"), uma descrição breve, e o tipo principal de métrica (NPS `0-10`, CSAT `1-5`, Usefulness `0-10`).
- **Lista de Sessões Ativas:** Todas as sessões criadas ficarão visíveis aqui.
- **Link Público:** Cada sessão recém criada ganha um **Link Público** único (ex: `http://localhost:8000/f/abcxyz`) que deve ser distribuído via WhatsApp, QRCode no slide ou Email.
- **Ações Rápidas:**
  - `Ver Detalhes`: Te leva para um raio-x profundo daquela sessão específica.
  - `Arquivar`: Oculta e encerra o link público dessa sessão permanentemente.

### Visão Profunda (`2_Session_Detail`)
> **Objetivo:** Auditar todos os insights qualitativos do público em segundos, com ajuda de Inteligência Artificial.

- **Resumo do Score:** Mostra a **Nota Média** e quantas pessoas responderam.
- **Analisar Resultados:** 
  - O sistema exibe um grande botão cinza chamado `Run / Analyze`.
  - Diferente do Google Forms (onde você teria que ler 100 textos na mão), clicar neste botão faz o App enviar *todos* os feedbacks textuais coletados para a Camada de IA (LiteLLM configurado para Ollama ou Gemini) ou, caso tudo falhe matematicamente, executar um Fallback Regra Fixa de sumarização. 
  - Em instantes, esse motor analisa todos os dados e retorna de forma humanizada o **Resumo Executivo** (um briefing da opinião majoritária coletada), os 3 **Principais Temas Positivos** e **Principais Temas Negativos**.
- **Exportação:** Após a análise preenchida ou mesmo durante ela, a página oferece dois botões definitivos:
  1. `Baixar Dados (CSV)`: Baixa os dados *crus* em formato compatível com Excel para BI.
  2. `Baixar Resumo (PDF)`: Prepara o texto executivo e emite uma documentação limpa formatada em `.pdf` listando NPS final, resumo e opiniões predominantes.

---

## 👩‍💻 3. Fluxo do Participante (Coleta de Dados)

Esse é o lado da moeda com o qual o seu usuário lida. O design é um fluxo puramente dinâmico "one-screen" focado em zero perdas e micro-experiências (sem precisar recarregar o sistema web).

1. **Iniciando:** O participante clica no Link Público pelo celular ou notebook e cai numa tela espoleta, sem login obrigatório, lendo o título do seu treinamento. Ao clicar em `Iniciar Feedback`, a API registra internamente a atividade no banco.
2. **Pergunta Principal (Score Direto):** O sistema aparece como uma bolha de chat e pergunta a métrica principal da sala (NPS ou CSAT). O usuário reage e *clica apenas na nota*. Imediatamente, sem "submit forms" tradicionais, a nota voa para o banco (gravando em caso de desistência prematura).
3. **Chat Dinâmico:** Uma segunda bolha de chat aparece na hora de forma adaptativa.
  - O sistema detecta: "Ele deu nota baixa?". A pergunta vira compreensiva: "Sinto muito. O que poderíamos ter feito de diferente?".
  - O participante expõe textual e organicamente seu pensamento e usa o botão `Enviar` (tudo injetado sem refresh ou loadings demorados).
4. **Resgate e Profundidade:** A engine continuará provocando por volta de **2 a 3 perguntas textuais sucessivas** complementares dependendo da densidade, e terminará se despedindo e agradecendo pelo tempo fornecido. 

---

## 🤖 4. Como a Inteligência Artificial Atua?

O agente está preparado para absorver IA de forma *Agnóstica* num pipeline robusto de contorno de falhas na camada `app/services/llm_client.py` operando LiteLLM com uma cascata de 3 camadas ativadas automaticamente sob o capô:

1. **Camada Local (Ollama - Custo $0):** Ao rodar a sumarização (`Analyze`), o sistema caça primeiro no `localhost:11434` (se houver o executável local instalando no seu ambiente) para processar o JSON na sua própria CPU/GPU privada, preservando privacidade zero e sem custos contínuos online.
2. **Fallback Nuvem (Gemini Free - Custo $0):** Caso você defina `GEMINI_API_KEY` num ambiente online, e o de cima falhar (ou se for o seu padrão produtivo de nuvem escalável) ele desvia o fluxo de geração massiva para do laboratório da Google, extraindo o resumo executivo sem exigir refatoração alguma num clique só.
3. **Dead End Fail-safe System (Offline Puro - Custo $0):** Caso não haja API configurada e nem o Ollama disponível — o seu Dashboard Administrativo *não quebra* com uma tela de "500 Server Error". Ele resgata todos os textos, escaneia dicionários e heurísticas fixas simples de NLP e lista estatisticamente pontos principais e quantifica citações — garantindo resiliência operacional constante no MVP.
