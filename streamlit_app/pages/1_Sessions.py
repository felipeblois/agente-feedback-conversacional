import pandas as pd
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
    render_session_card,
    render_sidebar,
    render_spotlight_card,
    render_stat_band,
    status_pill,
)


FEEDBACK_TYPE_OPTIONS = [
    "treinamento",
    "palestra",
    "cast",
    "workshop",
    "onboarding",
]


def matches_filters(session: dict, query: str, feedback_filter: str) -> bool:
    haystack = " ".join(
        [
            session.get("title") or "",
            session.get("description") or "",
            session.get("theme_summary") or "",
            session.get("session_goal") or "",
            session.get("target_audience") or "",
            session.get("topics_to_explore") or "",
        ]
    ).lower()
    query_ok = query.lower() in haystack if query else True
    type_ok = feedback_filter == "Todos" or session.get("score_type") == feedback_filter
    return query_ok and type_ok


configure_page("Sessoes", "S")
ensure_admin_access()
render_sidebar("sessions")

panel_header(
    "Workspace",
    "Sessoes de feedback",
    "Crie, filtre, ajuste o briefing e acompanhe a operacao sem sair do painel.",
)

try:
    sessions = api_get("/sessions")
except Exception as exc:
    st.error(f"Erro ao conectar com a API: {exc}")
    sessions = []

filter_cols = st.columns([1.6, 1, 0.9])
with filter_cols[0]:
    search_query = st.text_input("Buscar sessao", placeholder="Titulo, tema, publico ou objetivo")
with filter_cols[1]:
    feedback_filter = st.selectbox(
        "Filtrar por tipo",
        ["Todos"] + FEEDBACK_TYPE_OPTIONS,
        format_func=lambda value: "Todos os tipos" if value == "Todos" else value.replace("_", " ").title(),
    )
with filter_cols[2]:
    sort_mode = st.selectbox("Ordenar por", ["Mais recentes", "Mais respostas", "Maior conclusao"])

filtered_sessions = [item for item in sessions if matches_filters(item, search_query, feedback_filter)]
if sort_mode == "Mais respostas":
    filtered_sessions = sorted(filtered_sessions, key=lambda item: item["response_count"], reverse=True)
elif sort_mode == "Maior conclusao":
    filtered_sessions = sorted(filtered_sessions, key=lambda item: item["completion_rate"], reverse=True)

if filtered_sessions:
    lead_session = filtered_sessions[0]
    render_spotlight_card(
        "Sessao em foco",
        lead_session["title"],
        lead_session.get("description") or "Use esta area para acompanhar a sessao com maior prioridade operacional.",
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
            "label": "Sessoes ativas",
            "value": str(len(sessions)),
            "copy": "Base ativa carregada no admin.",
        },
        {
            "label": "Filtradas",
            "value": str(len(filtered_sessions)),
            "copy": "Resultado atual da busca.",
        },
        {
            "label": "Respostas",
            "value": str(sum(item["response_count"] for item in filtered_sessions)),
            "copy": "Volume somado das sessoes visiveis.",
        },
        {
            "label": "Analises",
            "value": str(sum(item["analysis_count"] for item in filtered_sessions)),
            "copy": "Analises ja concluidas nesse recorte.",
        },
    ]
)

list_col, form_col = st.columns([1.55, 1])

with list_col:
    st.markdown("### Lista operacional")
    if not sessions:
        empty_state(
            "Nenhuma sessao cadastrada",
            "Crie uma nova sessao para liberar o link publico e iniciar a coleta de feedback.",
        )
    elif not filtered_sessions:
        empty_state(
            "Nenhuma sessao encontrada",
            "Ajuste os filtros ou crie uma nova sessao para preencher esta lista.",
        )
    else:
        summary_df = pd.DataFrame(
            [
                {
                    "Sessao": item["title"],
                    "Criado por": item.get("created_by_admin_username") or "bootstrap",
                    "Tipo": str(item["score_type"]).replace("_", " ").title(),
                    "Respostas": item["response_count"],
                    "Conclusao": format_pct(item["completion_rate"]),
                    "Score medio": format_score(item.get("avg_score")),
                    "Ultima analise": format_dt(item.get("last_analysis_at")),
                }
                for item in filtered_sessions
            ]
        )
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

        for session in filtered_sessions:
            render_session_card(
                title=session["title"],
                description=session.get("description") or "Sem descricao cadastrada.",
                status_html=status_pill(session["status"]),
                chips=[
                    str(session.get("score_type", "")).replace("_", " ").title(),
                    session.get("theme_summary") or "Tema nao informado",
                    session.get("target_audience") or "Publico nao informado",
                    f"Criado por {session.get('created_by_admin_username') or 'bootstrap'}",
                ],
                facts=[
                    ("Respostas", str(session["response_count"])),
                    ("Conclusao", format_pct(session["completion_rate"])),
                    ("Score medio", format_score(session.get("avg_score"))),
                    ("Ultima analise", format_dt(session.get("last_analysis_at"))),
                    ("Criada em", format_dt(session.get("created_at"))),
                    ("Criado por", session.get("created_by_admin_username") or "bootstrap"),
                ],
            )
            action_cols = st.columns([1.05, 1.25, 1])
            with action_cols[0]:
                if st.button("Abrir detalhe", key=f"detail-{session['id']}", use_container_width=True):
                    st.session_state["selected_session_id"] = session["id"]
                    st.switch_page("pages/2_Session_Detail.py")
            with action_cols[1]:
                st.code(f"http://localhost:8000/f/{session['public_token']}")
            with action_cols[2]:
                if st.button("Arquivar", key=f"archive-{session['id']}", use_container_width=True):
                    try:
                        api_post(f"/sessions/{session['id']}/archive")
                        st.session_state["selected_archived_session_id"] = session["id"]
                        st.success("Sessao arquivada com sucesso.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Nao foi possivel arquivar: {exc}")

with form_col:
    st.markdown("### Criar sessao")
    st.caption("Crie uma nova coleta com briefing estruturado para a IA.")
    with st.form("new_session_form", clear_on_submit=True):
        title = st.text_input("Titulo")
        desc = st.text_area("Descricao")
        score_type = st.selectbox(
            "Tipo de feedback",
            FEEDBACK_TYPE_OPTIONS,
            format_func=lambda value: value.replace("_", " ").title(),
        )
        theme_summary = st.text_input("Tema principal")
        session_goal = st.text_area(
            "Objetivo da sessao",
            help="Explique o que voce quer validar ou aprender com os feedbacks.",
        )
        target_audience = st.text_input("Publico-alvo")
        topics_to_explore = st.text_area(
            "Topicos para explorar",
            help="Liste os assuntos que a IA deve priorizar ao aprofundar a conversa.",
        )
        ai_guidance = st.text_area(
            "Orientacoes extras para IA",
            help="Exemplo: evitar perguntas longas, focar em aplicabilidade pratica, explorar exemplos reais.",
        )
        max_followups = st.slider("Perguntas de aprofundamento", min_value=1, max_value=20, value=3)
        st.caption("Esse limite define o maximo de perguntas abertas que a IA pode fazer ao participante.")
        submitted = st.form_submit_button("Criar sessao", use_container_width=True)
        if submitted:
            if not title.strip():
                st.error("Informe um titulo para a sessao.")
            else:
                try:
                    created = api_post(
                        "/sessions",
                        {
                            "title": title,
                            "description": desc,
                            "score_type": score_type,
                            "theme_summary": theme_summary,
                            "session_goal": session_goal,
                            "target_audience": target_audience,
                            "topics_to_explore": topics_to_explore,
                            "ai_guidance": ai_guidance,
                            "is_anonymous": True,
                            "max_followup_questions": max_followups,
                        },
                    )
                    st.session_state["selected_session_id"] = created["id"]
                    st.success("Sessao criada com sucesso.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Erro ao criar sessao: {exc}")
