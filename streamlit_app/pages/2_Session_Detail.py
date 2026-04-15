from datetime import datetime
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
    push_flash,
)


ENGINE_OPTIONS = {
    "Gemini": {"provider": "gemini", "model": "gemini-2.5-flash", "label": "Gemini"},
    "ChatGPT": {"provider": "openai", "model": "gpt-4.1-mini", "label": "ChatGPT"},
    "Claude": {"provider": "anthropic", "model": "claude-3-5-haiku-20241022", "label": "Claude 3.5 Haiku"},
    "Jarvis": {"provider": "fallback", "label": "Jarvis"},
}

FEEDBACK_TYPE_OPTIONS = [
    "treinamento",
    "palestra",
    "cast",
    "workshop",
    "onboarding",
]

PUBLIC_LINK_STATUS_LABELS = {
    "active": "Ativo",
    "disabled": "Desabilitado",
    "revoked": "Revogado",
    "expired": "Expirado",
    "inactive": "Inativo",
}


def friendly_provider_name(provider: Optional[str], model: Optional[str] = None) -> str:
    normalized = (provider or "").lower()
    normalized_model = (model or "").lower()

    if normalized == "gemini":
        return "Gemini"
    if normalized == "openai" or "gpt" in normalized_model:
        return "ChatGPT"
    if normalized == "anthropic" or "claude" in normalized_model:
        return "Claude 3.5 Haiku"
    if normalized in {"fallback", "static_fallback", "llm_fallback_parse_error", "empty"}:
        return "Jarvis"
    return provider or "Auto"


def friendly_public_link_status(status: Optional[str]) -> str:
    return PUBLIC_LINK_STATUS_LABELS.get((status or "").lower(), status or "Desconhecido")


configure_page("Detalhe da sessao", "A")
ensure_admin_access()
render_sidebar("detail")

st.markdown(
    """
    <style>
        div[data-testid="stTabs"] button[role="tab"] {
            min-height: 48px;
            padding: 0.75rem 1.1rem;
            border-radius: 14px 14px 0 0;
            font-size: 0.98rem;
            font-weight: 700;
            color: #a6acc9;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(167, 176, 211, 0.10);
            transition: all 0.18s ease;
        }
        div[data-testid="stTabs"] button[role="tab"]:hover {
            color: #f2f4fb;
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(167, 176, 211, 0.16);
        }
        div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
            color: #f2f4fb;
            background: linear-gradient(180deg, rgba(74, 125, 255, 0.22), rgba(74, 125, 255, 0.10));
            border-color: rgba(74, 125, 255, 0.42);
            box-shadow: inset 0 -2px 0 rgba(74, 125, 255, 0.95);
        }
        div[data-testid="stTabs"] div[role="tablist"] {
            gap: 0.45rem;
            margin-bottom: 0.75rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

panel_header(
    "Insight center",
    "Detalhe da sessao",
    "Edite briefing, acompanhe a coleta e opere a sessao sem sair do painel.",
)

try:
    sessions = api_get("/sessions")
except Exception as exc:
    st.error(str(exc))
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
    st.error(str(exc))
    st.stop()

try:
    analysis = api_get(f"/sessions/{selected_id}/analysis")
except Exception:
    analysis = None

try:
    dashboard_summary = api_get("/sessions/dashboard/summary")
except Exception:
    dashboard_summary = {}

try:
    operational_audit = api_get("/settings/audit")
except Exception:
    operational_audit = {"items": []}

confirm_delete_key = f"confirm_delete_{selected_id}"
confirm_archive_key = f"confirm_archive_{selected_id}"
analysis_run_key = f"analysis_run_{selected_id}"
if confirm_delete_key not in st.session_state:
    st.session_state[confirm_delete_key] = False
if confirm_archive_key not in st.session_state:
    st.session_state[confirm_archive_key] = False
if analysis_run_key not in st.session_state:
    st.session_state[analysis_run_key] = False

render_spotlight_card(
    "Sessao ativa",
    detail["title"],
    detail.get("description") or "Sem descricao cadastrada para esta sessao.",
    [
        str(detail.get("score_type", "")).replace("_", " ").title(),
        detail.get("theme_summary") or "Tema nao informado",
        detail.get("target_audience") or "Publico nao informado",
        f"Criado por {detail.get('created_by_admin_username') or 'bootstrap'}",
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
    if st.button(
        "Gerar analise",
        use_container_width=True,
        disabled=st.session_state[analysis_run_key],
    ):
        st.session_state[analysis_run_key] = True
        st.rerun()
with header_cols[2]:
    if not st.session_state[confirm_archive_key]:
        if st.button(
            "Arquivar",
            use_container_width=True,
            disabled=st.session_state[analysis_run_key],
        ):
            st.session_state[confirm_archive_key] = True
            st.rerun()
with header_cols[3]:
    clipboard_button("Copiar link publico", detail["public_url"], f"copy-{selected_id}")

if st.session_state[analysis_run_key]:
    with st.spinner("Processando feedbacks da sessao..."):
        try:
            provider = ENGINE_OPTIONS[engine]["provider"]
            model = ENGINE_OPTIONS[engine].get("model")
            payload = {"provider": provider}
            if model:
                payload["model"] = model
            api_post(f"/sessions/{selected_id}/analyze", payload)
            push_flash("success", "Analise atualizada com sucesso.")
        except Exception as exc:
            push_flash("error", str(exc))
        finally:
            st.session_state[analysis_run_key] = False
    st.rerun()

if st.session_state[confirm_archive_key]:
    st.warning("Ao arquivar, a sessao sai da operacao ativa e vai para Sessoes Arquivadas.")
    archive_cols = st.columns([1, 1, 3])
    with archive_cols[0]:
        if st.button("Confirmar arquivamento", use_container_width=True):
            try:
                api_post(f"/sessions/{selected_id}/archive")
                st.session_state["selected_archived_session_id"] = selected_id
                st.session_state[confirm_archive_key] = False
                push_flash("success", "Sessao arquivada com sucesso.")
                st.switch_page("pages/4_Archived_Sessions.py")
            except Exception as exc:
                st.error(str(exc))
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
    recent_sessions = dashboard_summary.get("recent_sessions", [])
    portfolio_sessions = [item for item in recent_sessions if item.get("id") != selected_id]
    volume_rank = 1 + sum(1 for item in portfolio_sessions if item.get("response_count", 0) > detail["response_count"])
    score_rank = None
    if detail.get("avg_score") is not None:
        score_rank = 1 + sum(
            1
            for item in portfolio_sessions
            if item.get("avg_score") is not None and item.get("avg_score", 0) > detail.get("avg_score", 0)
        )
    session_audit_items = [
        item
        for item in operational_audit.get("items", [])
        if f"session_id={selected_id}" in (item.get("details") or "")
    ][:6]

    with main_col:
        render_session_card(
            title=detail["title"],
            description=detail.get("description") or "Sem descricao cadastrada.",
            status_html=status_pill(detail["status"]),
            chips=[
                str(detail.get("score_type", "")).replace("_", " ").title(),
                detail.get("target_audience") or "Publico nao informado",
                f"{detail.get('max_followup_questions')} aprofundamentos",
                f"Link {friendly_public_link_status(detail.get('public_link_status'))}",
            ],
            facts=[
                ("Tema", detail.get("theme_summary") or "Nao informado"),
                ("Objetivo", detail.get("session_goal") or "Nao informado"),
                ("Publico", detail.get("target_audience") or "Nao informado"),
                ("Criada", format_dt(detail.get("created_at"))),
                ("Criado por", detail.get("created_by_admin_username") or "bootstrap"),
                ("Ultima analise", format_dt(detail.get("last_analysis_at"))),
                ("Status do link", friendly_public_link_status(detail.get("public_link_status"))),
                ("Expira em", format_dt(detail.get("public_link_expires_at"))),
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
                    "copy": f"Autor: {detail.get('created_by_admin_username') or 'bootstrap'}",
                },
                {
                    "label": "Link publico",
                    "value": friendly_public_link_status(detail.get("public_link_status")),
                    "copy": format_dt(detail.get("public_link_expires_at")) or "Sem expiracao definida",
                },
            ],
            compact=True,
        )

        st.markdown("### Leitura comparativa")
        render_stat_band(
            [
                {
                    "label": "Rank em volume",
                    "value": f"#{volume_rank}",
                    "copy": "Posicao desta sessao no recorte mais recente.",
                },
                {
                    "label": "Rank em score",
                    "value": f"#{score_rank}" if score_rank is not None else "-",
                    "copy": "Comparativo do score medio atual.",
                },
                {
                    "label": "Media do portfolio",
                    "value": format_score(dashboard_summary.get("average_score")),
                    "copy": "Media das sessoes com analise concluida.",
                },
                {
                    "label": "Ativas no portfolio",
                    "value": str(dashboard_summary.get("active_sessions", 0)),
                    "copy": "Base ativa monitorada neste momento.",
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

        st.markdown("### Auditoria da sessao")
        if session_audit_items:
            for item in session_audit_items:
                render_insight_card(
                    f"{item.get('area', '-')} | {item.get('action', '-')}",
                    f"{format_dt(item.get('created_at'))} | {item.get('actor', '-')} | {item.get('details') or 'Sem detalhe adicional.'}",
                )
        else:
            empty_state(
                "Sem eventos rastreados",
                "As proximas alteracoes, analises e exportacoes desta sessao aparecerao aqui.",
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
    current_expiration = detail.get("public_link_expires_at")
    expiration_enabled_default = bool(current_expiration)
    expiration_date_default = (
        current_expiration.date() if isinstance(current_expiration, datetime) else datetime.now().date()
    )
    expiration_time_default = (
        current_expiration.time().replace(second=0, microsecond=0)
        if isinstance(current_expiration, datetime)
        else datetime.now().time().replace(second=0, microsecond=0)
    )
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
        st.markdown("#### Controle do link publico")
        public_link_enabled = st.toggle(
            "Link publico habilitado",
            value=detail.get("public_link_enabled", True),
            help="Quando desativado, o link deixa de aceitar novos acessos imediatamente.",
        )
        expiration_enabled = st.checkbox(
            "Definir expiracao do link publico",
            value=expiration_enabled_default,
            help="Use quando quiser que a sessao pare de aceitar respostas automaticamente.",
        )
        if expiration_enabled:
            expiration_cols = st.columns(2)
            with expiration_cols[0]:
                expiration_date = st.date_input("Data de expiracao", value=expiration_date_default)
            with expiration_cols[1]:
                expiration_time = st.time_input(
                    "Horario de expiracao",
                    value=expiration_time_default,
                    step=60,
                )
        else:
            expiration_date = None
            expiration_time = None
        submitted = st.form_submit_button("Salvar alteracoes", use_container_width=True)
        if submitted:
            try:
                public_link_expires_at = None
                if expiration_enabled and expiration_date and expiration_time:
                    public_link_expires_at = datetime.combine(
                        expiration_date,
                        expiration_time,
                    ).isoformat()
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
                        "public_link_enabled": public_link_enabled,
                        "public_link_expires_at": public_link_expires_at,
                    },
                )
                push_flash("success", "Sessao atualizada com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    st.markdown("### Controle do link publico")
    link_control_cols = st.columns(3)
    with link_control_cols[0]:
        if st.button("Revogar link", use_container_width=True):
            try:
                api_post(f"/sessions/{selected_id}/public-link/revoke")
                push_flash("success", "Link publico revogado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with link_control_cols[1]:
        if st.button("Reativar link", use_container_width=True):
            try:
                api_post(f"/sessions/{selected_id}/public-link/reactivate")
                push_flash("success", "Link publico reativado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    with link_control_cols[2]:
        if st.button("Gerar novo link", use_container_width=True):
            try:
                api_post(f"/sessions/{selected_id}/public-link/rotate")
                push_flash("success", "Novo link publico gerado com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    render_stat_band(
        [
            {
                "label": "Status do link",
                "value": friendly_public_link_status(detail.get("public_link_status")),
                "copy": "Controle atual de acesso publico.",
            },
            {
                "label": "Expiracao",
                "value": format_dt(detail.get("public_link_expires_at")) or "-",
                "copy": "Vazio significa link sem prazo automatico.",
            },
            {
                "label": "URL publica",
                "value": "Disponivel" if detail.get("public_link_enabled", True) else "Bloqueada",
                "copy": "Use revogar ou gerar novo link quando precisar cortar acesso.",
            },
        ],
        compact=True,
    )

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
                    push_flash("success", "Sessao excluida com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
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
    csv_ready_key = f"csv_export_ready_{selected_id}"
    pdf_ready_key = f"pdf_export_ready_{selected_id}"
    with export_cols[0]:
        if detail["response_count"] > 0:
            if st.button("Preparar CSV", key=f"prepare-csv-{selected_id}", use_container_width=True):
                try:
                    st.session_state[csv_ready_key] = api_get_bytes(f"/sessions/{selected_id}/export/csv")
                    push_flash("success", "CSV preparado para download.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            csv_bytes = st.session_state.get(csv_ready_key)
        else:
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
        if analysis:
            if st.button("Preparar PDF", key=f"prepare-pdf-{selected_id}", use_container_width=True):
                try:
                    st.session_state[pdf_ready_key] = api_get_bytes(f"/sessions/{selected_id}/export/pdf")
                    push_flash("success", "PDF preparado para download.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            pdf_bytes = st.session_state.get(pdf_ready_key)
        else:
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
