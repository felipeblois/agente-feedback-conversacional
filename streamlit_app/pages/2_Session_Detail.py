import pandas as pd
import plotly.express as px
import streamlit as st
from typing import Optional

from ui import (
    api_delete,
    api_get,
    api_get_bytes,
    api_post,
    clipboard_button,
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


ENGINE_OPTIONS = {
    "Gemini": {"provider": "gemini", "label": "Gemini"},
    "claude-3-5-haiku": {"provider": "anthropic", "label": "Claude 3.5 Haiku"},
    "Jarvis": {"provider": "fallback", "label": "Jarvis (Fallback local)"},
}


def friendly_provider_name(provider: Optional[str], model: Optional[str] = None) -> str:
    normalized = (provider or "").lower()
    normalized_model = (model or "").lower()

    if normalized == "gemini":
        return "Gemini"
    if normalized == "anthropic" or "claude" in normalized_model:
        return "Claude 3.5 Haiku"
    if normalized in {"fallback", "static_fallback", "llm_fallback_parse_error", "empty"}:
        return "Jarvis"
    return provider or "Auto"


configure_page("Detalhe da sessao", "📈")
render_sidebar("detail")

panel_header(
    "Insight center",
    "Detalhe da sessao",
    "Acompanhe desempenho da coleta, gere analise e exporte o material sem sair do painel.",
)

try:
    sessions = api_get("/sessions")
except Exception as exc:
    st.error(f"Nao foi possivel carregar as sessoes: {exc}")
    st.stop()

if not sessions:
    empty_state(
        "Nenhuma sessao encontrada",
        "Crie uma sessao antes de abrir a tela de detalhe.",
    )
    st.stop()

session_ids = [session["id"] for session in sessions]
default_session_id = st.session_state.get("selected_session_id", session_ids[0])
if default_session_id not in session_ids:
    default_session_id = session_ids[0]

selected_id = st.selectbox(
    "Selecione a sessao",
    options=session_ids,
    index=session_ids.index(default_session_id),
    format_func=lambda session_id: next(item["title"] for item in sessions if item["id"] == session_id),
)
st.session_state["selected_session_id"] = selected_id

try:
    detail = api_get(f"/sessions/{selected_id}/detail")
except Exception as exc:
    st.error(f"Nao foi possivel carregar o detalhe da sessao: {exc}")
    st.stop()

try:
    analysis = api_get(f"/sessions/{selected_id}/analysis")
except Exception:
    analysis = None

confirm_delete_key = f"confirm_delete_{selected_id}"
if confirm_delete_key not in st.session_state:
    st.session_state[confirm_delete_key] = False

header_cols = st.columns([3.3, 1.15, 1.15, 1.2])
with header_cols[0]:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-title">{detail['title']}</div>
            <p class="section-copy">{detail.get('description') or 'Sem descricao cadastrada.'}</p>
            <p class="section-copy">{status_pill(detail["status"])} <span style="margin-left:10px;color:#a6acc9;">Link publico ativo</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with header_cols[1]:
    engine = st.radio(
        "Motor de analise",
        options=list(ENGINE_OPTIONS.keys()),
        format_func=lambda key: ENGINE_OPTIONS[key]["label"],
        horizontal=False,
    )
with header_cols[2]:
    if st.button("Gerar analise", use_container_width=True):
        with st.spinner("Processando feedbacks da sessao..."):
            try:
                provider = ENGINE_OPTIONS[engine]["provider"]
                api_post(f"/sessions/{selected_id}/analyze", {"provider": provider})
                st.success("Analise atualizada com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Falha ao gerar analise: {exc}")
with header_cols[3]:
    clipboard_button("Copiar link publico", detail["public_url"], f"copy-{selected_id}")

danger_col, spacer_col = st.columns([1.2, 3.8])
with danger_col:
    if not st.session_state[confirm_delete_key]:
        if st.button("Excluir sessao", use_container_width=True):
            st.session_state[confirm_delete_key] = True
            st.rerun()

if st.session_state[confirm_delete_key]:
    st.warning("Essa acao remove a sessao, respostas, analises e exportacoes associadas.")
    confirm_cols = st.columns([1, 1, 3])
    with confirm_cols[0]:
        if st.button("Confirmar exclusao", use_container_width=True):
            try:
                current_index = session_ids.index(selected_id)
                api_delete(f"/sessions/{selected_id}")
                st.session_state[confirm_delete_key] = False
                remaining_ids = [session_id for session_id in session_ids if session_id != selected_id]

                if remaining_ids:
                    if current_index < len(remaining_ids):
                        st.session_state["selected_session_id"] = remaining_ids[current_index]
                    else:
                        st.session_state["selected_session_id"] = remaining_ids[-1]
                else:
                    st.session_state.pop("selected_session_id", None)
                st.success("Sessao excluida com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Nao foi possivel excluir a sessao: {exc}")
    with confirm_cols[1]:
        if st.button("Cancelar", use_container_width=True):
            st.session_state[confirm_delete_key] = False
            st.rerun()

with st.expander("Link publico e exportacoes", expanded=False):
    st.code(detail["public_url"])
    export_cols = st.columns(2)
    with export_cols[0]:
        try:
            csv_bytes = api_get_bytes(f"/sessions/{selected_id}/export/csv")
        except Exception:
            csv_bytes = None
        if csv_bytes:
            st.download_button(
                "Exportar CSV",
                data=csv_bytes,
                file_name=f"session_{selected_id}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.info("Sem respostas para exportar em CSV.")
    with export_cols[1]:
        try:
            pdf_bytes = api_get_bytes(f"/sessions/{selected_id}/export/pdf")
        except Exception:
            pdf_bytes = None
        if pdf_bytes:
            st.download_button(
                "Exportar PDF",
                data=pdf_bytes,
                file_name=f"session_{selected_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.info("Gere uma analise antes de exportar em PDF.")

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("💬", "Respostas", str(detail["response_count"]), "Total recebido", "teal")
with kpi_cols[1]:
    render_kpi_card("✓", "Concluidas", str(detail["completed_response_count"]), "Fluxos finalizados", "blue")
with kpi_cols[2]:
    render_kpi_card("◔", "Conclusao", format_pct(detail["completion_rate"]), "Conversas encerradas", "gold")
with kpi_cols[3]:
    render_kpi_card("★", "Score medio", format_score(detail.get("avg_score")), "Media das notas", "purple")

main_col, side_col = st.columns([1.5, 1])

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
            "Compartilhe o link publico para iniciar a coleta e preencher a distribuicao.",
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
            "Nenhuma resposta recebida",
            "Assim que os participantes responderem, a lista recente aparecera aqui.",
        )

with side_col:
    st.markdown("### Insights")
    if analysis:
        render_insight_card(
            "Resumo executivo",
            f'{analysis["summary"]} Motor: {friendly_provider_name(analysis.get("provider"), analysis.get("model"))} | Gerado em {format_dt(analysis.get("created_at"))}',
        )

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
            "Analise ainda nao gerada",
            "Use o botao de analise para produzir o resumo executivo e os temas principais desta sessao.",
        )
