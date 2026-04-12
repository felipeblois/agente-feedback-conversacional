import streamlit as st

from ui import (
    api_get,
    configure_page,
    empty_state,
    format_dt,
    format_pct,
    info_list,
    panel_header,
    render_kpi_card,
    render_quick_tiles,
    render_sessions_table,
    render_sidebar,
)


configure_page("Dashboard", "📊")
render_sidebar("dashboard")

panel_header(
    "Dashboard",
    "Agente de Feedback Conversacional",
    "Crie sessoes, acompanhe respostas e gere insights com IA.",
)

top_head, top_action = st.columns([5, 1.2])
with top_head:
    st.markdown("")
with top_action:
    if st.button("+ Nova sessao", use_container_width=True):
        st.switch_page("pages/1_Sessions.py")

try:
    summary = api_get("/sessions/dashboard/summary")
except Exception as exc:
    st.error(f"Nao foi possivel carregar o dashboard: {exc}")
    st.stop()

recent_sessions = summary.get("recent_sessions", [])
if not recent_sessions:
    empty_state(
        "Nenhuma sessao ativa criada ainda",
        "Crie sua primeira sessao para acompanhar respostas, taxa de conclusao e insights no dashboard.",
    )
    if st.button("Criar sessao agora"):
        st.switch_page("pages/1_Sessions.py")
    st.stop()

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("🗂", "Sessoes", str(summary["total_sessions"]), "Total monitorado", "blue")
with kpi_cols[1]:
    render_kpi_card("💬", "Respostas", str(summary["total_responses"]), "Base coletada", "teal")
with kpi_cols[2]:
    render_kpi_card(
        "◔",
        "Taxa de conclusao",
        format_pct(summary["average_completion_rate"]),
        f"{summary['completed_responses']} concluidas",
        "gold",
    )
with kpi_cols[3]:
    render_kpi_card(
        "🗃",
        "Arquivadas",
        str(summary["archived_sessions"]),
        format_dt(summary.get("last_analysis_at")) if summary.get("last_analysis_at") else "Sem analise recente",
        "purple",
    )

st.markdown("### Sessoes recentes")
render_sessions_table(recent_sessions)

left, right = st.columns([1.15, 1.35])
with left:
    st.markdown("### Resumo rapido")
    top_session = max(recent_sessions, key=lambda item: item["response_count"])
    best_completion = max(recent_sessions, key=lambda item: item["completion_rate"])
    info_list(
        [
            ("Sessoes ativas", f"{summary['active_sessions']} sessoes em andamento"),
            ("Sessoes arquivadas", f"{summary['archived_sessions']} sessoes preservadas"),
            ("Maior volume", f"{top_session['title']} com {top_session['response_count']} respostas"),
            ("Melhor conclusao", f"{best_completion['title']} com {format_pct(best_completion['completion_rate'])}"),
            ("Ultima leitura", f"Analise mais recente em {format_dt(summary.get('last_analysis_at'))}"),
        ]
    )

with right:
    st.markdown("### Atalhos rapidos")
    render_quick_tiles(
        [
            {"icon": "+", "title": "Nova Sessao", "copy": "Abra uma coleta e gere novo link publico."},
            {"icon": "▥", "title": "Ver Ultimo Detalhe", "copy": "Continue da sessao mais recente com um clique."},
        ]
    )
    if st.button("Abrir criacao", use_container_width=True):
        st.switch_page("pages/1_Sessions.py")
    if st.button("Abrir detalhe", use_container_width=True):
        st.session_state["selected_session_id"] = recent_sessions[0]["id"]
        st.switch_page("pages/2_Session_Detail.py")

    st.markdown("### Status da aplicacao")
    info_list(
        [
            ("Backend", "http://localhost:8000"),
            ("Banco de dados", "data/feedback_agent.db"),
            ("Modo", "Execucao local WSL"),
        ]
    )
