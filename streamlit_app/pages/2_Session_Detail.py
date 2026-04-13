from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from ui import (
    api_delete,
    api_get,
    api_get_bytes,
    api_patch,
    api_post,
    clipboard_button,
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
)


ENGINE_OPTIONS = {
    "Gemini": {"provider": "gemini", "label": "Gemini"},
    "claude-3-5-haiku": {"provider": "anthropic", "label": "Claude 3.5 Haiku"},
    "Jarvis": {"provider": "fallback", "label": "Jarvis"},
}

FEEDBACK_TYPE_OPTIONS = [
    "treinamento",
    "palestra",
    "cast",
    "workshop",
    "onboarding",
]


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


configure_page("Detalhe da sessao", "A")
ensure_admin_access()
render_sidebar("detail")

panel_header(
    "Insight center",
    "Detalhe da sessao",
    "Edite briefing, acompanhe a coleta e opere a sessao sem sair do painel.",
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
confirm_archive_key = f"confirm_archive_{selected_id}"
if confirm_delete_key not in st.session_state:
    st.session_state[confirm_delete_key] = False
if confirm_archive_key not in st.session_state:
    st.session_state[confirm_archive_key] = False

render_spotlight_card(
    "Sessao ativa",
    detail["title"],
    detail.get("description") or "Sem descricao cadastrada para esta sessao.",
    [
        str(detail.get("score_type", "")).replace("_", " ").title(),
        detail.get("theme_summary") or "Tema nao informado",
        detail.get("target_audience") or "Publico nao informado",
        f"Atualizada {format_dt(detail.get('updated_at'))}",
    ],
)

header_cols = st.columns([1.2, 1.2, 1, 1.2])
with header_cols[0]:
    engine = st.radio(
        "Motor de analise",
        options=list(ENGINE_OPTIONS.keys()),
        format_func=lambda key: ENGINE_OPTIONS[key]["label"],
        horizontal=False,
    )
with header_cols[1]:
    if st.button("Gerar analise", use_container_width=True):
        with st.spinner("Processando feedbacks da sessao..."):
            try:
                provider = ENGINE_OPTIONS[engine]["provider"]
                api_post(f"/sessions/{selected_id}/analyze", {"provider": provider})
                st.success("Analise atualizada com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Falha ao gerar analise: {exc}")
with header_cols[2]:
    if not st.session_state[confirm_archive_key]:
        if st.button("Arquivar", use_container_width=True):
            st.session_state[confirm_archive_key] = True
            st.rerun()
with header_cols[3]:
    clipboard_button("Copiar link publico", detail["public_url"], f"copy-{selected_id}")

if st.session_state[confirm_archive_key]:
    st.warning("Ao arquivar, a sessao sai da operacao ativa e vai para Sessoes Arquivadas.")
    archive_cols = st.columns([1, 1, 3])
    with archive_cols[0]:
        if st.button("Confirmar arquivamento", use_container_width=True):
            try:
                api_post(f"/sessions/{selected_id}/archive")
                st.session_state["selected_archived_session_id"] = selected_id
                st.session_state[confirm_archive_key] = False
                st.success("Sessao arquivada com sucesso.")
                st.switch_page("pages/4_Archived_Sessions.py")
            except Exception as exc:
                st.error(f"Nao foi possivel arquivar a sessao: {exc}")
    with archive_cols[1]:
        if st.button("Cancelar arquivamento", use_container_width=True):
            st.session_state[confirm_archive_key] = False
            st.rerun()

render_stat_band(
    [
        {
            "label": "Respostas",
            "value": str(detail["response_count"]),
            "copy": "Total recebido pela sessao.",
        },
        {
            "label": "Concluidas",
            "value": str(detail["completed_response_count"]),
            "copy": "Fluxos finalizados pelos participantes.",
        },
        {
            "label": "Conclusao",
            "value": format_pct(detail["completion_rate"]),
            "copy": "Taxa de conversa encerrada.",
        },
        {
            "label": "Score medio",
            "value": format_score(detail.get("avg_score")),
            "copy": "Media atual registrada.",
        },
    ]
)

kpi_cols = st.columns(4)
with kpi_cols[0]:
    render_kpi_card("RES", "Respostas", str(detail["response_count"]), "Total recebido", "teal")
with kpi_cols[1]:
    render_kpi_card("OK", "Concluidas", str(detail["completed_response_count"]), "Fluxos finalizados", "blue")
with kpi_cols[2]:
    render_kpi_card("TAX", "Conclusao", format_pct(detail["completion_rate"]), "Conversas encerradas", "gold")
with kpi_cols[3]:
    render_kpi_card("AVG", "Score medio", format_score(detail.get("avg_score")), "Media das notas", "purple")

overview_tab, briefing_tab, edit_tab, export_tab = st.tabs(
    ["Visao geral", "Briefing IA", "Editar sessao", "Exportacoes"]
)

with overview_tab:
    main_col, side_col = st.columns([1.5, 1])

    with main_col:
        render_session_card(
            title=detail["title"],
            description=detail.get("description") or "Sem descricao cadastrada.",
            status_html=status_pill(detail["status"]),
            chips=[
                str(detail.get("score_type", "")).replace("_", " ").title(),
                detail.get("target_audience") or "Publico nao informado",
                f"{detail.get('max_followup_questions')} aprofundamentos",
            ],
            facts=[
                ("Tema", detail.get("theme_summary") or "Nao informado"),
                ("Objetivo", detail.get("session_goal") or "Nao informado"),
                ("Publico", detail.get("target_audience") or "Nao informado"),
                ("Criada", format_dt(detail.get("created_at"))),
                ("Ultima analise", format_dt(detail.get("last_analysis_at"))),
                ("Link publico", detail["public_url"]),
            ],
        )

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
        st.markdown("### Resumo operacional")
        render_stat_band(
            [
                {
                    "label": "Publico-alvo",
                    "value": detail.get("target_audience") or "-",
                    "copy": "Faixa principal da sessao.",
                },
                {
                    "label": "Aprofundamento",
                    "value": str(detail.get("max_followup_questions")),
                    "copy": "Limite de perguntas abertas.",
                },
                {
                    "label": "Status",
                    "value": detail.get("status", "-").title(),
                    "copy": "Situacao operacional atual.",
                },
            ],
            compact=True,
        )

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
                render_insight_card(title, " | ".join(str(item) for item in items) if items else "Nenhum item disponivel no momento.")
        else:
            empty_state(
                "Analise ainda nao gerada",
                "Use o botao de analise para produzir o resumo executivo e os temas principais desta sessao.",
            )

with briefing_tab:
    render_session_card(
        title="Briefing estruturado",
        description="Informacoes que orientam a IA na conducão da conversa e na leitura operacional da sessao.",
        status_html=status_pill(detail["status"]),
        chips=[
            str(detail.get("score_type", "")).replace("_", " ").title(),
            detail.get("theme_summary") or "Tema nao informado",
        ],
        facts=[
            ("Tema principal", detail.get("theme_summary") or "Nao informado"),
            ("Objetivo", detail.get("session_goal") or "Nao informado"),
            ("Publico-alvo", detail.get("target_audience") or "Nao informado"),
            ("Topicos", detail.get("topics_to_explore") or "Nao informado"),
            ("Orientacoes IA", detail.get("ai_guidance") or "Nao informado"),
            ("Link publico", detail["public_url"]),
        ],
    )

with edit_tab:
    st.markdown("### Editar sessao")
    st.caption("Ajuste briefing, tipo de feedback e limite de aprofundamento sem recriar a sessao.")
    with st.form(f"edit_session_form_{selected_id}"):
        title = st.text_input("Titulo", value=detail.get("title") or "")
        description = st.text_area("Descricao", value=detail.get("description") or "")
        current_type = detail.get("score_type") or FEEDBACK_TYPE_OPTIONS[0]
        type_index = FEEDBACK_TYPE_OPTIONS.index(current_type) if current_type in FEEDBACK_TYPE_OPTIONS else 0
        score_type = st.selectbox(
            "Tipo de feedback",
            FEEDBACK_TYPE_OPTIONS,
            index=type_index,
            format_func=lambda value: value.replace("_", " ").title(),
        )
        theme_summary = st.text_input("Tema principal", value=detail.get("theme_summary") or "")
        session_goal = st.text_area("Objetivo da sessao", value=detail.get("session_goal") or "")
        target_audience = st.text_input("Publico-alvo", value=detail.get("target_audience") or "")
        topics_to_explore = st.text_area("Topicos para explorar", value=detail.get("topics_to_explore") or "")
        ai_guidance = st.text_area("Orientacoes extras para IA", value=detail.get("ai_guidance") or "")
        max_followup_questions = st.slider(
            "Perguntas de aprofundamento",
            min_value=1,
            max_value=20,
            value=int(detail.get("max_followup_questions") or 3),
        )
        submitted = st.form_submit_button("Salvar alteracoes", use_container_width=True)
        if submitted:
            try:
                api_patch(
                    f"/sessions/{selected_id}",
                    {
                        "title": title,
                        "description": description,
                        "score_type": score_type,
                        "theme_summary": theme_summary,
                        "session_goal": session_goal,
                        "target_audience": target_audience,
                        "topics_to_explore": topics_to_explore,
                        "ai_guidance": ai_guidance,
                        "max_followup_questions": max_followup_questions,
                    },
                )
                st.success("Sessao atualizada com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Nao foi possivel atualizar a sessao: {exc}")

    st.markdown("### Zona sensivel")
    danger_cols = st.columns([1, 2.2])
    with danger_cols[0]:
        if not st.session_state[confirm_delete_key]:
            if st.button("Excluir sessao", use_container_width=True):
                st.session_state[confirm_delete_key] = True
                st.rerun()
    with danger_cols[1]:
        st.caption("Exclusao remove sessao, respostas, analises e exportacoes associadas.")

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
                        st.session_state["selected_session_id"] = remaining_ids[current_index] if current_index < len(remaining_ids) else remaining_ids[-1]
                    else:
                        st.session_state.pop("selected_session_id", None)
                    st.success("Sessao excluida com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Nao foi possivel excluir a sessao: {exc}")
        with confirm_cols[1]:
            if st.button("Cancelar exclusao", use_container_width=True):
                st.session_state[confirm_delete_key] = False
                st.rerun()

with export_tab:
    render_spotlight_card(
        "Distribuicao",
        "Link publico e exportacoes",
        "Compartilhe a sessao ou baixe os dados para operacao, auditoria e leitura executiva.",
        [detail["public_url"], f"Criada em {format_dt(detail.get('created_at'))}"],
    )
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
            empty_state("CSV indisponivel", "Sem respostas para exportar em CSV.")
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
            empty_state("PDF indisponivel", "Gere uma analise antes de exportar em PDF.")
