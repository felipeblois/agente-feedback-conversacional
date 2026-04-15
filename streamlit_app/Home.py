import streamlit as st

from ui import (
    api_get,
    configure_page,
    empty_state,
    ensure_admin_access,
    format_pct,
    format_score,
    info_list,
    panel_header,
    render_kpi_card,
    render_sessions_table,
    render_sidebar,
    render_stat_band,
)


configure_page("Dashboard", "D")
ensure_admin_access()
render_sidebar("dashboard")

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 0.2rem;
            padding-bottom: 1.1rem;
        }
        .hero-card .eyebrow {
            display: none;
        }
        .hero-card {
            padding: 14px 18px 10px 18px;
            margin-bottom: 0.65rem;
        }
        .hero-card .panel-title {
            font-size: 3rem;
            letter-spacing: -0.03em;
            margin: 0;
        }
        .hero-card .panel-subtitle {
            display: none;
        }
        .stMarkdown h3 {
            margin-top: 0.8rem;
            margin-bottom: 0.45rem;
            padding-top: 0;
        }
        div[data-testid="stHorizontalBlock"] {
            gap: 1rem;
        }
        div[data-testid="stDataFrame"] {
            margin-top: 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

panel_header(
    "",
    "InsightFlow Dashboard",
    "",
)

try:
    summary = api_get("/sessions/dashboard/summary")
    ai_settings = api_get("/settings/ai")
except Exception as exc:
    st.error(str(exc))
    st.stop()

recent_sessions = summary.get("recent_sessions", [])
top_session = max(recent_sessions, key=lambda item: item["response_count"]) if recent_sessions else None
best_completion = max(recent_sessions, key=lambda item: item["completion_rate"]) if recent_sessions else None

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
            "value": str(top_session["response_count"]) if top_session else "0",
            "copy": top_session["title"] if top_session else "Sem sessao com volume ainda",
        },
        {
            "label": "Melhor conclusao",
            "value": format_pct(best_completion["completion_rate"]) if best_completion else "0%",
            "copy": best_completion["title"] if best_completion else "Sem sessao concluida ainda",
        },
        {
            "label": "Score medio em foco",
            "value": format_score(top_session.get("avg_score")) if top_session else "-",
            "copy": "Leitura media do portfolio recente.",
        },
    ]
)

st.markdown("### Sessoes recentes")
if recent_sessions:
    render_sessions_table(recent_sessions)
else:
    empty_state(
        "Nenhuma sessao ativa criada ainda",
        "Crie sua primeira sessao para acompanhar respostas, conclusao e leitura executiva no dashboard.",
    )

left, right = st.columns([1.15, 1.35], gap="large")
with left:
    st.markdown("### Resumo executivo")
    info_list(
        [
            ("Operacao atual", f"{summary['active_sessions']} sessoes ativas, {summary['total_responses']} respostas e {summary['analyses_completed']} analises acumuladas"),
            ("Lider em volume", summary.get("response_leader_title") or (top_session["title"] if top_session else "Ainda sem sessao lider")),
            ("Lider em conclusao", summary.get("completion_leader_title") or (best_completion["title"] if best_completion else "Ainda sem sessao lider")),
            ("Melhor score medio", summary.get("score_leader_title") or "Ainda sem sessao lider em score"),
            ("Historico preservado", f"{summary['archived_sessions']} sessoes arquivadas para consulta futura"),
        ]
    )
    st.markdown("### Highlights gerenciais")
    highlights = summary.get("executive_highlights", [])
    if highlights:
        info_list([(f"{index + 1}. Insight", item) for index, item in enumerate(highlights)])
    else:
        empty_state("Sem highlights ainda", "As leituras gerenciais aparecerao aqui conforme as sessoes forem sendo operadas.")

with right:
    st.markdown("### Saude do ambiente")
    info_list(
        [
            ("Motor principal", {"gemini": "Gemini", "openai": "OpenAI", "anthropic": "Claude", "fallback": "Jarvis"}.get(ai_settings.get("default_provider"), ai_settings.get("default_provider", "-"))),
            ("Motor de fallback", {"gemini": "Gemini", "openai": "OpenAI", "anthropic": "Claude", "fallback": "Jarvis"}.get(ai_settings.get("fallback_provider"), ai_settings.get("fallback_provider", "-"))),
            ("Gemini", "Configurado" if ai_settings.get("gemini_key_configured") else "Nao configurado"),
            ("OpenAI", "Configurado" if ai_settings.get("openai_key_configured") else "Nao configurado"),
            ("Anthropic", "Configurado" if ai_settings.get("anthropic_key_configured") else "Nao configurado"),
        ]
    )
