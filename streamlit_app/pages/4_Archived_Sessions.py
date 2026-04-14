import pandas as pd
import plotly.express as px
import streamlit as st

from ui import (
    api_get,
    api_post,
    configure_page,
    empty_state,
    ensure_admin_access,
    format_dt,
    format_pct,
    format_score,
    panel_header,
    render_insight_card,
    render_kpi_card,
    render_session_card,
    render_sidebar,
    render_spotlight_card,
    render_stat_band,
    status_pill,
    push_flash,
)


FEEDBACK_TYPE_OPTIONS = [
    "Todos",
    "treinamento",
    "palestra",
    "cast",
    "workshop",
    "onboarding",
]


configure_page("Sessoes arquivadas", "R")
ensure_admin_access()
render_sidebar("archived")

panel_header(
    "InsightFlow",
    "Historico arquivado",
    "Consulte o historico operacional, revise insights gerados e reative uma sessao quando precisar.",
)

try:
    archived_sessions = api_get("/sessions?status=archived")
except Exception as exc:
    st.error(str(exc))
    st.stop()

if not archived_sessions:
    empty_state(
        "Nenhuma sessao arquivada",
        "As sessoes arquivadas aparecerao aqui para consulta e eventual reativacao.",
    )
    st.stop()

search_col, filter_col = st.columns([2.4, 1.2])
with search_col:
    search_term = st.text_input("Buscar sessoes arquivadas", placeholder="Titulo, tema ou publico")
with filter_col:
    feedback_type = st.selectbox(
        "Tipo de feedback",
        FEEDBACK_TYPE_OPTIONS,
        format_func=lambda value: value.replace("_", " ").title(),
    )

filtered_archived = []
for session in archived_sessions:
    searchable = " ".join(
        [
            str(session.get("title") or ""),
            str(session.get("description") or ""),
            str(session.get("theme_summary") or ""),
            str(session.get("target_audience") or ""),
        ]
    ).lower()
    matches_search = not search_term or search_term.lower() in searchable
    matches_type = feedback_type == "Todos" or session.get("score_type") == feedback_type
    if matches_search and matches_type:
        filtered_archived.append(session)

if not filtered_archived:
    empty_state(
        "Nenhuma sessao encontrada",
        "Ajuste os filtros para localizar uma sessao arquivada.",
    )
    st.stop()

lead_session = filtered_archived[0]
render_spotlight_card(
    "Arquivo operacional",
    lead_session["title"],
    lead_session.get("description") or "Sessao arquivada pronta para consulta e eventual reativacao.",
    [
        str(lead_session.get("score_type", "")).replace("_", " ").title(),
        f"{lead_session['response_count']} respostas",
        f"{format_pct(lead_session['completion_rate'])} de conclusao",
        lead_session.get("target_audience") or "Publico nao informado",
    ],
)

render_stat_band(
    [
        {
            "label": "Arquivadas",
            "value": str(len(archived_sessions)),
            "copy": "Sessoes preservadas no historico.",
        },
        {
            "label": "Filtradas",
            "value": str(len(filtered_archived)),
            "copy": "Resultado atual da busca.",
        },
        {
            "label": "Respostas",
            "value": str(sum(item["response_count"] for item in filtered_archived)),
            "copy": "Volume total das sessoes visiveis.",
        },
        {
            "label": "Analises",
            "value": str(sum(item["analysis_count"] for item in filtered_archived)),
            "copy": "Leituras concluidas no historico.",
        },
    ]
)

archived_ids = [session["id"] for session in filtered_archived]
default_archived_id = st.session_state.get("selected_archived_session_id", archived_ids[0])
if default_archived_id not in archived_ids:
    default_archived_id = archived_ids[0]

selected_id = st.selectbox(
    "Selecione a sessao arquivada",
    options=archived_ids,
    index=archived_ids.index(default_archived_id),
    format_func=lambda session_id: next(item["title"] for item in filtered_archived if item["id"] == session_id),
)
st.session_state["selected_archived_session_id"] = selected_id

try:
    detail = api_get(f"/sessions/{selected_id}/detail")
except Exception as exc:
    st.error(str(exc))
    st.stop()

try:
    analysis = api_get(f"/sessions/{selected_id}/analysis")
except Exception:
    analysis = None

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("ARC", "Arquivadas", str(len(archived_sessions)), "Sessoes no historico", "blue")
with kpi_cols[1]:
    render_kpi_card("RES", "Respostas", str(detail["response_count"]), "Volume da sessao", "teal")
with kpi_cols[2]:
    render_kpi_card("TAX", "Conclusao", format_pct(detail["completion_rate"]), "Fluxos encerrados", "gold")
with kpi_cols[3]:
    render_kpi_card("AVG", "Score medio", format_score(detail.get("avg_score")), "Media registrada", "purple")

header_cols = st.columns([3.3, 1.2])
with header_cols[0]:
    render_session_card(
        title=detail["title"],
        description=detail.get("description") or "Sem descricao cadastrada.",
        status_html=status_pill(detail["status"]),
        chips=[
            str(detail.get("score_type", "")).replace("_", " ").title(),
            detail.get("theme_summary") or "Tema nao informado",
            detail.get("target_audience") or "Publico nao informado",
        ],
        facts=[
            ("Criada", format_dt(detail.get("created_at"))),
            ("Ultima analise", format_dt(detail.get("last_analysis_at"))),
            ("Objetivo", detail.get("session_goal") or "Nao informado"),
            ("Topicos", detail.get("topics_to_explore") or "Nao informado"),
            ("Respostas", str(detail["response_count"])),
            ("Conclusao", format_pct(detail["completion_rate"])),
        ],
    )
with header_cols[1]:
    if st.button("Reativar sessao", use_container_width=True):
        try:
            api_post(f"/sessions/{selected_id}/reactivate")
            st.session_state["selected_session_id"] = selected_id
            st.session_state.pop("selected_archived_session_id", None)
            push_flash("success", "Sessao reativada com sucesso.")
            st.switch_page("pages/2_Session_Detail.py")
        except Exception as exc:
            st.error(str(exc))

main_col, side_col = st.columns([1.55, 1])

with main_col:
    st.markdown("### Distribuicao de notas")
    distribution = detail.get("score_distribution", [])
    if distribution:
        chart_df = pd.DataFrame(distribution)
        fig = px.bar(
            chart_df,
            x="score",
            y="count",
            text="count",
            template="plotly_dark",
            color_discrete_sequence=["#4f7cff"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        empty_state(
            "Sem notas registradas",
            "Essa sessao foi arquivada sem distribuicao de notas disponivel.",
        )

    st.markdown("### Respostas recentes")
    recent_responses = detail.get("recent_responses", [])
    if recent_responses:
        response_df = pd.DataFrame(
            [
                {
                    "Participante": item["participant_label"],
                    "Score": item["score"] if item["score"] is not None else "-",
                    "Status": item["status"].title(),
                    "Ultima mensagem": item["latest_message"] or "Sem resposta textual ainda",
                    "Inicio": format_dt(item["started_at"]),
                }
                for item in recent_responses
            ]
        )
        st.dataframe(response_df, use_container_width=True, hide_index=True)
    else:
        empty_state(
            "Sem respostas arquivadas",
            "Ainda nao ha respostas vinculadas a esta sessao no historico.",
        )

with side_col:
    st.markdown("### Historico da sessao")
    render_stat_band(
        [
            {
                "label": "Tipo",
                "value": str(detail.get("score_type", "")).replace("_", " ").title() or "-",
                "copy": "Modelo de feedback da sessao.",
            },
            {
                "label": "Publico-alvo",
                "value": detail.get("target_audience") or "-",
                "copy": "Quem participou da coleta.",
            },
            {
                "label": "Aprofundamento",
                "value": str(detail.get("max_followup_questions")),
                "copy": "Limite configurado no briefing.",
            },
        ],
        compact=True,
    )

    st.markdown("### Insights")
    if analysis:
        render_insight_card("Resumo executivo", analysis.get("summary") or "Sem resumo disponivel.")
        insight_sections = [
            ("Temas positivos", analysis.get("top_positive_themes", [])),
            ("Temas negativos", analysis.get("top_negative_themes", [])),
            ("Principais elogios", analysis.get("positives", [])),
            ("Principais criticas", analysis.get("negatives", [])),
            ("Recomendacoes", analysis.get("recommendations", [])),
        ]
        for title, items in insight_sections:
            render_insight_card(title, " | ".join(str(item) for item in items) if items else "Nenhum item disponivel no momento.")
    else:
        empty_state(
            "Sem analise registrada",
            "A sessao foi arquivada sem uma analise persistida para consulta.",
        )
