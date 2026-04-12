import pandas as pd
import plotly.express as px
import streamlit as st

from ui import (
    api_get,
    api_post,
    configure_page,
    empty_state,
    format_dt,
    format_pct,
    format_score,
    panel_header,
    render_insight_card,
    render_kpi_card,
    render_sidebar,
    status_pill,
)


configure_page("Sessoes arquivadas", "🗃️")
render_sidebar("archived")

panel_header(
    "Arquivo",
    "Sessoes arquivadas",
    "Consulte o historico da operacao, revise insights gerados e reative uma sessao quando precisar.",
)

try:
    archived_sessions = api_get("/sessions?status=archived")
except Exception as exc:
    st.error(f"Nao foi possivel carregar as sessoes arquivadas: {exc}")
    st.stop()

if not archived_sessions:
    empty_state(
        "Nenhuma sessao arquivada",
        "As sessoes arquivadas aparecerao aqui para consulta e eventual reativacao.",
    )
    st.stop()

archived_ids = [session["id"] for session in archived_sessions]
default_archived_id = st.session_state.get("selected_archived_session_id", archived_ids[0])
if default_archived_id not in archived_ids:
    default_archived_id = archived_ids[0]

selected_id = st.selectbox(
    "Selecione a sessao arquivada",
    options=archived_ids,
    index=archived_ids.index(default_archived_id),
    format_func=lambda session_id: next(
        item["title"] for item in archived_sessions if item["id"] == session_id
    ),
)
st.session_state["selected_archived_session_id"] = selected_id

try:
    detail = api_get(f"/sessions/{selected_id}/detail")
except Exception as exc:
    st.error(f"Nao foi possivel carregar o detalhe da sessao arquivada: {exc}")
    st.stop()

try:
    analysis = api_get(f"/sessions/{selected_id}/analysis")
except Exception:
    analysis = None

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("🗃", "Arquivadas", str(len(archived_sessions)), "Sessoes no historico", "blue")
with kpi_cols[1]:
    render_kpi_card("💬", "Respostas", str(detail["response_count"]), "Volume da sessao", "teal")
with kpi_cols[2]:
    render_kpi_card("◔", "Conclusao", format_pct(detail["completion_rate"]), "Fluxos encerrados", "gold")
with kpi_cols[3]:
    render_kpi_card("★", "Score medio", format_score(detail.get("avg_score")), "Media registrada", "purple")

header_cols = st.columns([3.3, 1.2])
with header_cols[0]:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-title">{detail['title']}</div>
            <p class="section-copy">{detail.get('description') or 'Sem descricao cadastrada.'}</p>
            <p class="section-copy">{status_pill(detail["status"])} <span style="margin-left:10px;color:#a6acc9;">Sessao preservada no historico</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_cols[1]:
    if st.button("Reativar sessao", use_container_width=True):
        try:
            api_post(f"/sessions/{selected_id}/reactivate")
            st.session_state["selected_session_id"] = selected_id
            st.session_state.pop("selected_archived_session_id", None)
            st.success("Sessao reativada com sucesso.")
            st.switch_page("pages/2_Session_Detail.py")
        except Exception as exc:
            st.error(f"Nao foi possivel reativar a sessao: {exc}")

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
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-title">Contexto</div>
            <p class="section-copy">Criada em {format_dt(detail.get("created_at"))}</p>
            <p class="section-copy">Ultima analise em {format_dt(detail.get("last_analysis_at"))}</p>
            <p class="section-copy">Tipo de feedback {str(detail.get("score_type", "")).replace("_", " ").title()}</p>
            <p class="section-copy">Tema principal {detail.get("theme_summary") or "Nao informado"}</p>
            <p class="section-copy">Objetivo {detail.get("session_goal") or "Nao informado"}</p>
        </div>
        """,
        unsafe_allow_html=True,
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
            if items:
                render_insight_card(title, " • ".join(str(item) for item in items))
            else:
                render_insight_card(title, "Nenhum item disponivel no momento.")
    else:
        empty_state(
            "Sem analise registrada",
            "A sessao foi arquivada sem uma analise persistida para consulta.",
        )
