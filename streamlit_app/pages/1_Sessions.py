import pandas as pd
import streamlit as st

from ui import (
    api_delete,
    api_get,
    api_post,
    configure_page,
    empty_state,
    format_dt,
    format_pct,
    format_score,
    panel_header,
    render_sidebar,
    status_pill,
)


configure_page("Sessoes", "🗂️")
render_sidebar("sessions")

panel_header(
    "Workspace",
    "Sessoes de feedback",
    "Crie novas sessoes, acompanhe volume de respostas e entre nos detalhes com um clique.",
)

try:
    sessions = api_get("/sessions")
except Exception as exc:
    st.error(f"Erro ao conectar com a API: {exc}")
    sessions = []

top_cols = st.columns([1, 1, 1, 1])
top_cols[0].metric("Sessoes", len(sessions))
top_cols[1].metric("Ativas", sum(1 for item in sessions if item["status"] == "active"))
top_cols[2].metric("Respostas", sum(item["response_count"] for item in sessions))
top_cols[3].metric(
    "Analises",
    sum(item["analysis_count"] for item in sessions),
)

list_col, form_col = st.columns([1.5, 1])

with list_col:
    st.markdown("### Lista de sessoes")
    if not sessions:
        empty_state(
            "Nenhuma sessao cadastrada",
            "Crie uma nova sessao para liberar o link publico e iniciar a coleta de feedback.",
        )
    else:
        summary_df = pd.DataFrame(
            [
                {
                    "Sessao": item["title"],
                    "Status": item["status"].title(),
                    "Respostas": item["response_count"],
                    "Conclusao": format_pct(item["completion_rate"]),
                    "Score medio": format_score(item.get("avg_score")),
                    "Ultima analise": format_dt(item.get("last_analysis_at")),
                }
                for item in sessions
            ]
        )
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        for session in sessions:
            st.markdown(
                f"""
                <div class="panel-card">
                    <div class="section-title">{session["title"]}</div>
                    <p class="section-copy">{session.get("description") or "Sem descricao"}</p>
                    <p class="section-copy">{status_pill(session["status"])} | {session["response_count"]} respostas | {format_pct(session["completion_rate"])} concluidas</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            action_cols = st.columns([1, 1, 1, 1])
            with action_cols[0]:
                if st.button("Detalhes", key=f"detail-{session['id']}", use_container_width=True):
                    st.session_state["selected_session_id"] = session["id"]
                    st.switch_page("pages/2_Session_Detail.py")
            with action_cols[1]:
                st.code(f"http://localhost:8000/f/{session['public_token']}")
            with action_cols[2]:
                st.caption(f"Score: {format_score(session.get('avg_score'))}")
            with action_cols[3]:
                if st.button("Arquivar", key=f"archive-{session['id']}", use_container_width=True):
                    try:
                        api_delete(f"/sessions/{session['id']}")
                        st.success("Sessao arquivada com sucesso.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Nao foi possivel arquivar: {exc}")

with form_col:
    st.markdown("### Criar sessao")
    st.caption("Novo link publico para sua proxima coleta.")
    with st.form("new_session_form", clear_on_submit=True):
        title = st.text_input("Titulo")
        desc = st.text_area("Descricao")
        score_type = st.selectbox("Tipo de nota", ["nps", "csat", "usefulness"])
        max_followups = st.slider("Perguntas de aprofundamento", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button("Criar sessao", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Informe um titulo para a sessao.")
            else:
                try:
                    api_post(
                        "/sessions",
                        {
                            "title": title,
                            "description": desc,
                            "score_type": score_type,
                            "is_anonymous": True,
                            "max_followup_questions": max_followups,
                        },
                    )
                    st.success("Sessao criada com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erro ao criar sessao: {exc}")
