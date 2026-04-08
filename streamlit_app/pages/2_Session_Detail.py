import streamlit as st
import httpx
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Detalhes da Sessão", page_icon="📊", layout="wide")

API_BASE = "http://localhost:8000/api/v1"

st.title("Detalhes da Sessão")

try:
    with httpx.Client() as client:
        res = client.get(f"{API_BASE}/sessions")
        sessions = res.json()
except:
    sessions = []
    
if not sessions:
    st.warning("Nenhuma sessão encontrada. Vá para a página de Sessões.")
    st.stop()

session_opts = {s["id"]: s["title"] for s in sessions}
selected_id = st.selectbox("Selecione uma sessão", options=list(session_opts.keys()), format_func=lambda x: session_opts[x])


st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Análise com IA")
    if st.button("Run / Analyze (Ollama/Gemini)"):
        with st.spinner("Analisando..."):
            try:
                with httpx.Client(timeout=60.0) as client:
                    res = client.post(f"{API_BASE}/sessions/{selected_id}/analyze", json={})
                    if res.status_code == 200:
                        st.success("Análise atualizada!")
                    else:
                        st.error(f"Erro: {res.text}")
            except Exception as e:
                st.error(f"Falha na requisição: {e}")
                
    # Fetch Analysis
    analysis = None
    try:
        with httpx.Client() as client:
            res = client.get(f"{API_BASE}/sessions/{selected_id}/analysis")
            if res.status_code == 200:
                analysis = res.json()
    except:
        pass
        
    if analysis:
        avg = analysis.get("avg_score")
        if avg:
            st.metric("Score Médio", f"{avg:.2f}")
        
        st.write("### Resumo Executivo")
        st.write(analysis["summary"])
        
        st.write("### Top Temas Positivos")
        for t in analysis.get("top_positive_themes", []):
            st.markdown(f"- {t}")
            
        st.write("### Top Temas Negativos")
        for t in analysis.get("top_negative_themes", []):
            st.markdown(f"- {t}")

with col2:
    st.subheader("Exportações")
    try:
        with httpx.Client() as client:
            # Download CSV
            csv_res = client.get(f"{API_BASE}/sessions/{selected_id}/export/csv")
            if csv_res.status_code == 200:
                st.download_button("Baixar Dados (CSV)", data=csv_res.content, file_name=f"session_{selected_id}.csv", mime="text/csv")
            else:
                st.info("Nenhuma resposta para baixar.")
                
            pdf_res = client.get(f"{API_BASE}/sessions/{selected_id}/export/pdf")
            if pdf_res.status_code == 200:
                st.download_button("Baixar Resumo (PDF)", data=pdf_res.content, file_name=f"report_session_{selected_id}.pdf", mime="application/pdf")
    except Exception as e:
        st.error("Serviço offline.")
