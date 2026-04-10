from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import html
import httpx
import streamlit as st
import streamlit.components.v1 as components


API_BASE = "http://localhost:8000/api/v1"


def configure_page(title: str, icon: str) -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    inject_theme()


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #12131c;
                --bg-2: #181a26;
                --panel: #202332;
                --panel-soft: #262a3b;
                --panel-hover: #2b3044;
                --border: rgba(167, 176, 211, 0.12);
                --text: #f2f4fb;
                --muted: #a6acc9;
                --accent: #4a7dff;
                --accent-2: #5b8cff;
                --success: #36c58f;
                --warning: #d3a85c;
                --purple: #8e59ff;
                --teal: #4eb9b1;
                --card-shadow: 0 22px 46px rgba(0, 0, 0, 0.24);
            }

            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background:
                    linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0)),
                    linear-gradient(180deg, #161721 0%, #171925 100%);
                color: var(--text);
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(39, 41, 55, 0.98), rgba(26, 28, 40, 0.98));
                border-right: 1px solid var(--border);
            }

            [data-testid="stSidebar"] * {
                color: var(--text);
            }

            [data-testid="stSidebar"] .stButton > button {
                background: rgba(255,255,255,0.03);
                border: 1px solid transparent;
                justify-content: flex-start;
            }

            [data-testid="stSidebar"] .stButton > button:hover {
                background: rgba(255,255,255,0.06);
                border-color: var(--border);
            }

            [data-testid="stMetric"] {
                background: linear-gradient(180deg, rgba(35, 38, 53, 0.96), rgba(30, 33, 46, 0.98));
                border: 1px solid var(--border);
                border-radius: 20px;
                padding: 14px 16px;
                box-shadow: var(--card-shadow);
            }

            div[data-testid="stMetricLabel"] {
                color: var(--muted);
                font-weight: 600;
            }

            div[data-testid="stMetricValue"] {
                color: var(--text);
            }

            .panel-card {
                background: linear-gradient(180deg, rgba(35, 38, 53, 0.96), rgba(30, 33, 46, 0.98));
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 20px;
                box-shadow: var(--card-shadow);
                margin-bottom: 1rem;
            }

            .hero-card {
                background: linear-gradient(180deg, rgba(24, 26, 38, 0.98), rgba(26, 28, 42, 1));
                border: 1px solid var(--border);
                border-radius: 26px;
                padding: 28px 30px;
                margin-bottom: 1.2rem;
                box-shadow: var(--card-shadow);
            }

            .eyebrow {
                color: #8ea8ff;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.76rem;
                font-weight: 700;
            }

            .panel-title {
                color: var(--text);
                font-size: 2.2rem;
                font-weight: 700;
                margin: 0.3rem 0 0.45rem 0;
                line-height: 1.12;
            }

            .panel-subtitle {
                color: var(--muted);
                margin-bottom: 0;
                font-size: 1rem;
                line-height: 1.5;
            }

            .section-title {
                color: var(--text);
                font-size: 1.1rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
            }

            .section-copy {
                color: var(--muted);
                font-size: 0.95rem;
                margin-bottom: 0;
                line-height: 1.5;
            }

            .status-pill {
                display: inline-block;
                border-radius: 999px;
                padding: 0.34rem 0.7rem;
                font-size: 0.78rem;
                font-weight: 700;
                border: 1px solid var(--border);
                background: rgba(255,255,255,0.06);
                color: var(--text);
            }

            .status-pill.active {
                background: rgba(54, 197, 143, 0.16);
                color: #87f0bf;
                border-color: rgba(54, 197, 143, 0.32);
            }

            .status-pill.completed {
                background: rgba(74, 125, 255, 0.16);
                color: #bfceff;
                border-color: rgba(74, 125, 255, 0.32);
            }

            .status-pill.warning {
                background: rgba(211, 168, 92, 0.15);
                color: #f4d28d;
                border-color: rgba(211, 168, 92, 0.30);
            }

            .mini-list {
                display: grid;
                gap: 0.65rem;
            }

            .mini-item {
                padding: 0.95rem 1rem;
                border-radius: 14px;
                border: 1px solid var(--border);
                background: rgba(255,255,255,0.04);
            }

            .mini-item strong {
                display: block;
                color: var(--text);
                margin-bottom: 0.25rem;
            }

            .mini-item span {
                color: var(--muted);
                font-size: 0.92rem;
            }

            .empty-state {
                text-align: center;
                padding: 2.2rem 1.5rem;
                border-radius: 20px;
                border: 1px dashed rgba(167, 176, 211, 0.20);
                background: rgba(32, 35, 50, 0.76);
            }

            .empty-state h3 {
                color: var(--text);
                margin-bottom: 0.5rem;
            }

            .empty-state p {
                color: var(--muted);
                margin-bottom: 0;
            }

            .stButton > button {
                border-radius: 12px;
                border: 1px solid rgba(74, 125, 255, 0.28);
                background: linear-gradient(180deg, rgba(74,125,255,0.95), rgba(58,103,223,1));
                color: white;
                font-weight: 700;
                padding: 0.62rem 1rem;
                box-shadow: 0 10px 24px rgba(74, 125, 255, 0.22);
            }

            .stButton > button:hover {
                border-color: rgba(161, 185, 255, 0.5);
                color: white;
                background: linear-gradient(180deg, rgba(92,140,255,0.98), rgba(64,111,236,1));
            }

            .stSelectbox label, .stRadio label, .stTextInput label, .stTextArea label {
                color: var(--muted);
                font-weight: 600;
            }

            .stDataFrame, [data-testid="stTable"] {
                border: 1px solid var(--border);
                border-radius: 16px;
                overflow: hidden;
            }

            .kpi-card {
                display: flex;
                align-items: center;
                gap: 16px;
                padding: 18px;
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(35, 38, 53, 0.96), rgba(28, 31, 44, 0.98));
                border: 1px solid var(--border);
                box-shadow: var(--card-shadow);
                min-height: 108px;
            }

            .kpi-icon {
                width: 54px;
                height: 54px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.45rem;
                color: white;
                flex-shrink: 0;
            }

            .kpi-body {
                display: flex;
                flex-direction: column;
                gap: 0.2rem;
            }

            .kpi-label {
                color: var(--muted);
                font-size: 0.95rem;
                font-weight: 600;
            }

            .kpi-value {
                color: var(--text);
                font-size: 1.7rem;
                font-weight: 700;
                line-height: 1.1;
            }

            .kpi-meta {
                color: var(--muted);
                font-size: 0.85rem;
            }

            .table-shell {
                border: 1px solid var(--border);
                border-radius: 18px;
                background: linear-gradient(180deg, rgba(35, 38, 53, 0.98), rgba(28, 31, 44, 0.98));
                overflow: hidden;
                box-shadow: var(--card-shadow);
            }

            .table-head, .table-row {
                display: grid;
                grid-template-columns: 2.2fr 0.95fr 1fr 0.8fr 1fr;
                gap: 16px;
                align-items: center;
            }

            .table-head {
                padding: 0.95rem 1.2rem;
                color: var(--muted);
                font-size: 0.88rem;
                border-bottom: 1px solid var(--border);
                background: rgba(255,255,255,0.03);
            }

            .table-row {
                padding: 1rem 1.2rem;
                border-bottom: 1px solid rgba(167, 176, 211, 0.08);
            }

            .table-row:last-child {
                border-bottom: none;
            }

            .row-title {
                color: var(--text);
                font-weight: 600;
                font-size: 0.98rem;
                margin-bottom: 0.2rem;
            }

            .row-sub {
                color: var(--muted);
                font-size: 0.84rem;
            }

            .badge-chip {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.38rem 0.7rem;
                border-radius: 10px;
                font-size: 0.82rem;
                font-weight: 700;
                border: 1px solid transparent;
            }

            .badge-chip.success {
                color: #95f0c6;
                background: rgba(54, 197, 143, 0.16);
                border-color: rgba(54, 197, 143, 0.24);
            }

            .badge-chip.pending {
                color: #f4d28d;
                background: rgba(211, 168, 92, 0.16);
                border-color: rgba(211, 168, 92, 0.24);
            }

            .quick-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 14px;
            }

            .quick-tile {
                border-radius: 16px;
                border: 1px solid var(--border);
                background: rgba(255,255,255,0.04);
                padding: 1.2rem 1rem;
                min-height: 120px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                box-shadow: var(--card-shadow);
            }

            .quick-icon {
                font-size: 1.7rem;
                color: #dfe6ff;
            }

            .quick-title {
                color: var(--text);
                font-weight: 700;
                font-size: 1rem;
                margin-top: 1rem;
            }

            .quick-copy {
                color: var(--muted);
                font-size: 0.86rem;
                line-height: 1.4;
            }

            .insight-card {
                border-radius: 18px;
                border: 1px solid var(--border);
                background: linear-gradient(180deg, rgba(35, 38, 53, 0.96), rgba(28, 31, 44, 0.98));
                padding: 18px;
                box-shadow: var(--card-shadow);
                margin-bottom: 1rem;
            }

            .insight-heading {
                color: var(--text);
                font-weight: 700;
                margin-bottom: 0.65rem;
                font-size: 1rem;
            }

            .insight-list {
                margin: 0;
                padding-left: 1rem;
                color: var(--muted);
            }

            .sidebar-block {
                border: 1px solid var(--border);
                border-radius: 16px;
                background: rgba(255,255,255,0.04);
                padding: 0.95rem;
                margin-top: 1rem;
            }

            .sidebar-title {
                font-weight: 700;
                color: var(--text);
                margin-bottom: 0.35rem;
            }

            .sidebar-copy {
                color: var(--muted);
                font-size: 0.86rem;
                line-height: 1.45;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(current_page: str) -> None:
    st.sidebar.markdown("## Implantar")
    nav_items = [
        ("dashboard", "Dashboard", "◧", "streamlit_app/Home.py"),
        ("sessions", "Sessoes", "🗂", "pages/1_Sessions.py"),
        ("detail", "Analises", "📊", "pages/2_Session_Detail.py"),
    ]
    for key, label, icon, page in nav_items:
        if key == current_page:
            st.sidebar.markdown(f"### {icon} {label}")
        elif st.sidebar.button(f"{icon}  {label}", key=f"nav-{key}", use_container_width=True):
            st.switch_page(page)

    st.sidebar.markdown("")
    st.sidebar.markdown(
        """
        <div class="sidebar-block">
            <div class="sidebar-title">Workspace local</div>
            <div class="sidebar-copy">Painel administrativo do agente com operacao em FastAPI, Streamlit e SQLite.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")
    st.sidebar.caption("⚙ Configuracoes em breve")


def panel_header(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="eyebrow">{eyebrow}</div>
            <div class="panel-title">{title}</div>
            <p class="panel-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="section-title">{title}</div>
            <p class="section-copy">{copy}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_list(items: Iterable[tuple[str, str]]) -> None:
    markup = "".join(
        f'<div class="mini-item"><strong>{title}</strong><span>{value}</span></div>'
        for title, value in items
    )
    st.markdown(f'<div class="mini-list">{markup}</div>', unsafe_allow_html=True)


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="empty-state">
            <h3>{title}</h3>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(status: str) -> str:
    normalized = (status or "").lower()
    css_class = "warning"
    if normalized == "active":
        css_class = "active"
    elif normalized == "completed":
        css_class = "completed"
    return f'<span class="status-pill {css_class}">{html.escape(status.title())}</span>'


def analysis_badge(count: int) -> str:
    if count > 0:
        return '<span class="badge-chip success">Analise concluida</span>'
    return '<span class="badge-chip pending">Analise pendente</span>'


def format_pct(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.0f}%"


def format_score(value: Optional[float]) -> str:
    if value is None:
        return "-"
    return f"{value:.1f}"


def format_dt(value: Optional[str | datetime]) -> str:
    if not value:
        return "-"
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d/%m %H:%M")


def api_get(path: str) -> Any:
    with httpx.Client(timeout=30.0) as client:
        response = client.get(f"{API_BASE}{path}")
        response.raise_for_status()
        return response.json()


def api_post(path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{API_BASE}{path}", json=payload or {})
        response.raise_for_status()
        return response.json()


def api_delete(path: str) -> Any:
    with httpx.Client(timeout=30.0) as client:
        response = client.delete(f"{API_BASE}{path}")
        response.raise_for_status()
        return response.json() if response.content else None


def api_get_bytes(path: str) -> bytes:
    with httpx.Client(timeout=60.0) as client:
        response = client.get(f"{API_BASE}{path}")
        response.raise_for_status()
        return response.content


def clipboard_button(label: str, value: str, key: str) -> None:
    components.html(
        f"""
        <button
            id="{key}"
            style="
                width:100%;
                padding:0.75rem 1rem;
                border:none;
                border-radius:12px;
                background:linear-gradient(180deg, rgba(74,125,255,0.95), rgba(58,103,223,1));
                color:white;
                font-weight:700;
                cursor:pointer;
                box-shadow:0 10px 24px rgba(74,125,255,0.22);
            "
            onclick="navigator.clipboard.writeText({value!r}); this.innerText='Copiado';"
        >
            {html.escape(label)}
        </button>
        """,
        height=56,
    )


def render_kpi_card(icon: str, label: str, value: str, meta: str, tone: str) -> None:
    tone_map = {
        "blue": "linear-gradient(180deg, rgba(74,125,255,0.5), rgba(74,125,255,0.35))",
        "teal": "linear-gradient(180deg, rgba(78,185,177,0.5), rgba(78,185,177,0.35))",
        "gold": "linear-gradient(180deg, rgba(211,168,92,0.5), rgba(211,168,92,0.35))",
        "purple": "linear-gradient(180deg, rgba(142,89,255,0.5), rgba(142,89,255,0.35))",
    }
    bg = tone_map.get(tone, tone_map["blue"])
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon" style="background:{bg};">{html.escape(icon)}</div>
            <div class="kpi-body">
                <div class="kpi-label">{html.escape(label)}</div>
                <div class="kpi-value">{html.escape(value)}</div>
                <div class="kpi-meta">{html.escape(meta)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sessions_table(rows: Iterable[Dict[str, Any]]) -> None:
    items = list(rows)
    if not items:
        empty_state("Sem sessoes recentes", "Crie uma sessao para preencher a operacao do painel.")
        return

    row_html = []
    for row in items:
        row_html.append(
            f"""
            <div class="table-row">
                <div>
                    <div class="row-title">{html.escape(row["title"])}</div>
                    <div class="row-sub">{html.escape(row.get("description") or "Sem descricao cadastrada")}</div>
                </div>
                <div>
                    <div class="row-title">{html.escape(str(row["score_type"]).upper())}</div>
                    <div class="row-sub">{html.escape(format_score(row.get("avg_score")))} score medio</div>
                </div>
                <div>
                    {analysis_badge(row.get("analysis_count", 0))}
                    <div class="row-sub" style="margin-top:0.45rem;">{html.escape(str(row["response_count"]))} respostas</div>
                </div>
                <div>
                    <div class="row-title">{html.escape(format_dt(row.get("created_at")))}</div>
                    <div class="row-sub">{html.escape(format_pct(row.get("completion_rate")))} concluido</div>
                </div>
                <div>
                    <div class="row-title">{status_pill(row["status"])}</div>
                    <div class="row-sub" style="margin-top:0.45rem;">{html.escape(format_dt(row.get("last_analysis_at")))}</div>
                </div>
            </div>
            """
        )

    table_markup = f"""
    <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    background: transparent;
                    color: #f2f4fb;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                }}

                .table-shell {{
                    border: 1px solid rgba(167, 176, 211, 0.12);
                    border-radius: 18px;
                    background: linear-gradient(180deg, rgba(35, 38, 53, 0.98), rgba(28, 31, 44, 0.98));
                    overflow: hidden;
                    box-shadow: 0 22px 46px rgba(0, 0, 0, 0.24);
                }}

                .table-head, .table-row {{
                    display: grid;
                    grid-template-columns: 2.2fr 0.95fr 1fr 0.8fr 1fr;
                    gap: 16px;
                    align-items: center;
                }}

                .table-head {{
                    padding: 0.95rem 1.2rem;
                    color: #a6acc9;
                    font-size: 0.88rem;
                    border-bottom: 1px solid rgba(167, 176, 211, 0.12);
                    background: rgba(255,255,255,0.03);
                }}

                .table-row {{
                    padding: 1rem 1.2rem;
                    border-bottom: 1px solid rgba(167, 176, 211, 0.08);
                }}

                .table-row:last-child {{
                    border-bottom: none;
                }}

                .row-title {{
                    color: #f2f4fb;
                    font-weight: 600;
                    font-size: 0.98rem;
                    margin-bottom: 0.2rem;
                }}

                .row-sub {{
                    color: #a6acc9;
                    font-size: 0.84rem;
                }}

                .badge-chip {{
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0.38rem 0.7rem;
                    border-radius: 10px;
                    font-size: 0.82rem;
                    font-weight: 700;
                    border: 1px solid transparent;
                }}

                .badge-chip.success {{
                    color: #95f0c6;
                    background: rgba(54, 197, 143, 0.16);
                    border-color: rgba(54, 197, 143, 0.24);
                }}

                .badge-chip.pending {{
                    color: #f4d28d;
                    background: rgba(211, 168, 92, 0.16);
                    border-color: rgba(211, 168, 92, 0.24);
                }}

                .status-pill {{
                    display: inline-block;
                    border-radius: 999px;
                    padding: 0.34rem 0.7rem;
                    font-size: 0.78rem;
                    font-weight: 700;
                    border: 1px solid rgba(167, 176, 211, 0.12);
                    background: rgba(255,255,255,0.06);
                    color: #f2f4fb;
                }}

                .status-pill.active {{
                    background: rgba(54, 197, 143, 0.16);
                    color: #87f0bf;
                    border-color: rgba(54, 197, 143, 0.32);
                }}

                .status-pill.completed {{
                    background: rgba(74, 125, 255, 0.16);
                    color: #bfceff;
                    border-color: rgba(74, 125, 255, 0.32);
                }}

                .status-pill.warning {{
                    background: rgba(211, 168, 92, 0.15);
                    color: #f4d28d;
                    border-color: rgba(211, 168, 92, 0.30);
                }}
            </style>
        </head>
        <body>
            <div class="table-shell">
                <div class="table-head">
                    <div>Titulo</div>
                    <div>Tipo</div>
                    <div>Respostas</div>
                    <div>Criada em</div>
                    <div>Esperado</div>
                </div>
                {''.join(row_html)}
            </div>
        </body>
    </html>
    """

    row_count = max(len(items), 1)
    components.html(
        table_markup,
        height=96 + (row_count * 96),
        scrolling=False,
    )


def render_quick_tiles(items: Iterable[Dict[str, str]]) -> None:
    tile_items = list(items)
    if not tile_items:
        return

    tiles = "".join(
        f"""
        <div class="quick-tile">
            <div class="quick-icon">{html.escape(item['icon'])}</div>
            <div>
                <div class="quick-title">{html.escape(item['title'])}</div>
                <div class="quick-copy">{html.escape(item['copy'])}</div>
            </div>
        </div>
        """
        for item in tile_items
    )

    components.html(
        f"""
        <html>
            <head>
                <style>
                    body {{
                        margin: 0;
                        background: transparent;
                        color: #f2f4fb;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    }}

                    .quick-grid {{
                        display: grid;
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                        gap: 14px;
                    }}

                    .quick-tile {{
                        border-radius: 16px;
                        border: 1px solid rgba(167, 176, 211, 0.12);
                        background: rgba(255,255,255,0.04);
                        padding: 1.2rem 1rem;
                        min-height: 120px;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                        box-shadow: 0 22px 46px rgba(0, 0, 0, 0.24);
                    }}

                    .quick-icon {{
                        font-size: 1.7rem;
                        color: #dfe6ff;
                    }}

                    .quick-title {{
                        color: #f2f4fb;
                        font-weight: 700;
                        font-size: 1rem;
                        margin-top: 1rem;
                    }}

                    .quick-copy {{
                        color: #a6acc9;
                        font-size: 0.86rem;
                        line-height: 1.4;
                    }}
                </style>
            </head>
            <body>
                <div class="quick-grid">{tiles}</div>
            </body>
        </html>
        """,
        height=160,
        scrolling=False,
    )


def render_insight_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-heading">{html.escape(title)}</div>
            <div class="section-copy">{html.escape(body)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
