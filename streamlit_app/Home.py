import streamlit as st

from ui import (
    ADMIN_BASE_URL,
    PUBLIC_BASE_URL,
    api_get,
    configure_page,
    empty_state,
    ensure_admin_access,
    format_dt,
    format_pct,
    format_score,
    info_list,
    panel_header,
    render_kpi_card,
    render_quick_tiles,
    render_sessions_table,
    render_sidebar,
    render_spotlight_card,
    render_stat_band,
    push_flash,
)


configure_page("Dashboard", "D")
ensure_admin_access()
render_sidebar("dashboard")

panel_header(
    "InsightFlow",
    "Painel executivo de feedback conversacional",
    "Acompanhe operacao, leitura executiva e comparativos entre sessoes com narrativa pronta para demo e piloto.",
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
    st.error(str(exc))
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

top_session = max(recent_sessions, key=lambda item: item["response_count"])
best_completion = max(recent_sessions, key=lambda item: item["completion_rate"])

render_spotlight_card(
    "Sessao em destaque",
    top_session["title"],
    top_session.get("description") or "Sessao com maior movimento recente para demonstracao e acompanhamento.",
    [
        f"{top_session['response_count']} respostas",
        f"{format_pct(top_session['completion_rate'])} de conclusao",
        str(top_session.get("score_type", "")).replace("_", " ").title(),
        f"Analise {format_dt(top_session.get('last_analysis_at'))}",
    ],
)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("SES", "Sessoes", str(summary["total_sessions"]), "Total monitorado", "blue")
with kpi_cols[1]:
    render_kpi_card("FB", "Respostas", str(summary["total_responses"]), "Base coletada", "teal")
with kpi_cols[2]:
    render_kpi_card(
        "TAX",
        "Taxa de conclusao",
        format_pct(summary["average_completion_rate"]),
        f"{summary['completed_responses']} concluidas",
        "gold",
    )
with kpi_cols[3]:
    render_kpi_card(
        "ARC",
        "Score portfolio",
        format_score(summary.get("average_score")),
        f"{summary['sessions_with_analysis']} sessoes com analise",
        "purple",
    )

render_stat_band(
    [
        {
            "label": "Sessoes ativas",
            "value": str(summary["active_sessions"]),
            "copy": "Operando agora no painel.",
        },
        {
            "label": "Maior volume",
            "value": str(top_session["response_count"]),
            "copy": top_session["title"],
        },
        {
            "label": "Melhor conclusao",
            "value": format_pct(best_completion["completion_rate"]),
            "copy": best_completion["title"],
        },
        {
            "label": "Score medio em foco",
            "value": format_score(top_session.get("avg_score")),
            "copy": "Sessao com maior tracao recente.",
        },
    ]
)

st.markdown("### Sessoes recentes")
render_sessions_table(recent_sessions)

left, right = st.columns([1.15, 1.35])
with left:
    st.markdown("### Resumo executivo")
    info_list(
        [
            ("Operacao atual", f"{summary['active_sessions']} sessoes ativas, {summary['total_responses']} respostas e {summary['analyses_completed']} analises acumuladas"),
            ("Lider em volume", summary.get("response_leader_title") or top_session["title"]),
            ("Lider em conclusao", summary.get("completion_leader_title") or best_completion["title"]),
            ("Melhor score medio", summary.get("score_leader_title") or "Ainda sem sessao lider em score"),
            ("Historico preservado", f"{summary['archived_sessions']} sessoes arquivadas para consulta futura"),
        ]
    )
    st.markdown("### Highlights gerenciais")
    info_list([(f"{index + 1}. Insight", item) for index, item in enumerate(summary.get("executive_highlights", []))])
    st.markdown("### Narrativa de demo")
    info_list(
        [
            ("1. Estruture a sessao", "Monte o briefing com tema, publico e objetivo de negocio."),
            ("2. Colete feedback com IA", "Compartilhe o link e mostre a conversa guiada pelo contexto."),
            ("3. Leia e compare", "Use o detalhe e o dashboard para mostrar insight e comparativo gerencial."),
        ]
    )

with right:
    st.markdown("### Atalhos rapidos")
    render_quick_tiles(
        [
            {"icon": "+", "title": "Nova sessao", "copy": "Abra uma nova rodada de feedback com briefing estruturado."},
            {"icon": "[]", "title": "Abrir painel da sessao", "copy": "Continue a leitura executiva a partir da sessao mais recente."},
        ]
    )
    if st.button("Criar nova sessao", use_container_width=True):
        st.switch_page("pages/1_Sessions.py")
    if st.button("Abrir sessao em destaque", use_container_width=True):
        st.session_state["selected_session_id"] = recent_sessions[0]["id"]
        push_flash("info", "Sessao em destaque aberta para continuar a operacao.")
        st.switch_page("pages/2_Session_Detail.py")
    if st.button("Ver sessoes arquivadas", use_container_width=True):
        st.switch_page("pages/4_Archived_Sessions.py")

    st.markdown("### Pronto para piloto")
    info_list(
        [
            ("Entrada publica", PUBLIC_BASE_URL),
            ("Painel admin", ADMIN_BASE_URL),
            ("Base de dados", "SQLite local ou Postgres cloud"),
            ("Modo operacional", "WSL, EC2 ou cloud low-cost"),
        ]
    )
