import streamlit as st
import os

st.set_page_config(
    page_title="Feedback Agent MVP",
    page_icon="💬",
    layout="wide"
)

st.title("Agente de Feedback Conversacional")

st.markdown("""
### Bem-vindo ao MVP!
Este é o painel de administração local. Aqui você pode:

1. **Sessões:** Criar novas sessões de feedback e gerenciar as existentes.
2. **Detalhes:** Ver as respostas em tempo real, gerar resumos com IA e ver insights.
3. **Exportar:** Baixar os dados brutos e relatórios gerados.

Use o menu lateral para navegar.

---
**Status da Aplicação**
- Backend: `http://localhost:8000`
- Banco de dados: `data/feedback_agent.db`
""")
