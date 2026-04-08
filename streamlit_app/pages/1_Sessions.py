import streamlit as st
import httpx

st.set_page_config(page_title="Sessões", page_icon="📝", layout="wide")

API_BASE = "http://localhost:8000/api/v1"

st.title("Gerenciamento de Sessões")

# List Sessions
st.subheader("Sessões Ativas")

try:
    with httpx.Client() as client:
        res = client.get(f"{API_BASE}/sessions")
        sessions = res.json()
except Exception as e:
    st.error(f"Erro ao conectar com API: {e}")
    sessions = []

if sessions:
    for s in sessions:
        with st.expander(f"{s['title']} ({s['status']})"):
            st.write(f"**Descrição:** {s.get('description', '')}")
            public_url = f"http://localhost:8000/f/{s['public_token']}"
            st.write(f"**Link Público:** {public_url}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Ver Detalhes", key=f"det_{s['id']}"):
                    st.switch_page("pages/2_Session_Detail.py")
            with col2:
                if st.button("Arquivar", key=f"arch_{s['id']}"):
                    with httpx.Client() as c:
                        c.delete(f"{API_BASE}/sessions/{s['id']}")
                    st.rerun()
else:
    st.info("Nenhuma sessão cadastrada.")

# Add Session
st.divider()
st.subheader("Nova Sessão")

with st.form("new_session_form"):
    title = st.text_input("Título")
    desc = st.text_area("Descrição")
    score_type = st.selectbox("Tipo de Nota", ["nps", "csat", "usefulness"])
    
    submitted = st.form_submit_button("Criar Sessão")
    if submitted and title:
        try:
            with httpx.Client() as client:
                client.post(f"{API_BASE}/sessions", json={
                    "title": title,
                    "description": desc,
                    "score_type": score_type,
                    "is_anonymous": True,
                    "max_followup_questions": 3
                })
            st.success("Criado com sucesso!")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao criar: {e}")

