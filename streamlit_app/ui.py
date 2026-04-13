from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Optional

import html
import httpx
import streamlit as st
import streamlit.components.v1 as components

from app.core.config import get_settings
from app.core.security import get_admin_api_token, get_admin_runtime_meta

settings = get_settings()

API_BASE = f"{settings.api_base_url_clean}/api/v1"
PUBLIC_BASE_URL = settings.public_base_url_clean
ADMIN_BASE_URL = settings.admin_base_url_clean
AUTH_STATE_KEY = "admin_authenticated"
AUTH_TOKEN_KEY = "admin_api_token"
AUTH_ACTOR_KEY = "admin_actor"


def configure_page(title: str, icon: str) -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    inject_theme()


def ensure_admin_access() -> None:
    if st.session_state.get(AUTH_STATE_KEY):
        return

    meta = get_admin_runtime_meta()
    st.markdown(
        """
        <style>
            .auth-shell {
                max-width: 520px;
                margin: 7vh auto 0 auto;
                padding: 28px;
                border-radius: 24px;
                border: 1px solid rgba(167, 176, 211, 0.14);
                background: linear-gradient(180deg, rgba(28, 31, 44, 0.98), rgba(21, 23, 33, 0.98));
                box-shadow: 0 22px 46px rgba(0, 0, 0, 0.28);
            }
            .auth-title {
                color: #f2f4fb;
                font-size: 1.8rem;
                font-weight: 700;
                margin-bottom: 0.4rem;
            }
            .auth-copy {
                color: #a6acc9;
                line-height: 1.5;
                margin-bottom: 1rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="auth-shell">
            <div class="auth-title">Acesso do admin</div>
            <div class="auth-copy">
                Painel protegido da instancia <strong>{html.escape(str(meta["instance_name"]))}</strong>.
                Entre com suas credenciais para continuar.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("admin_login_form"):
        username = st.text_input("Usuario", value=meta["admin_username"])
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
        if submitted:
            try:
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        f"{API_BASE}/settings/admin/login",
                        json={"username": username, "password": password},
                    )
                    response.raise_for_status()
                    payload = response.json()
                st.session_state[AUTH_STATE_KEY] = True
                st.session_state[AUTH_TOKEN_KEY] = payload["token"]
                st.session_state[AUTH_ACTOR_KEY] = payload["actor"]
                st.success("Acesso liberado com sucesso.")
                st.rerun()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 401:
                    st.error("Credenciais invalidas.")
                elif exc.response.status_code == 503:
                    st.warning("A API esta acordando no Render. Aguarde alguns segundos e tente novamente.")
                else:
                    st.error(f"Nao foi possivel autenticar agora. API respondeu com status {exc.response.status_code}.")
            except httpx.TimeoutException:
                st.warning("A API demorou para responder. Em ambiente free no Render isso pode acontecer ao acordar o servico.")
            except httpx.RequestError:
                st.error(f"Nao foi possivel conectar na API configurada em {API_BASE}.")
            except Exception as exc:
                st.error(f"Falha inesperada ao autenticar: {exc.__class__.__name__}")

    if meta.get("uses_default_password"):
        st.warning(
            "Esta instancia ainda usa a senha padrao do admin. Antes de comercializar, altere ADMIN_PASSWORD no .env."
        )
    st.stop()


def render_logout_control() -> None:
    if st.sidebar.button("Sair", key="logout-admin", use_container_width=True):
        st.session_state.pop(AUTH_STATE_KEY, None)
        st.session_state.pop(AUTH_TOKEN_KEY, None)
        st.session_state.pop(AUTH_ACTOR_KEY, None)
        st.rerun()


def _admin_headers() -> Dict[str, str]:
    token = st.session_state.get(AUTH_TOKEN_KEY) or get_admin_api_token()
    return {"X-Admin-Token": token}


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

            .stSelectbox label,
            .stRadio label,
            .stTextInput label,
            .stTextArea label,
            .stSlider label {
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
                font-size: 1.05rem;
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

            .spotlight-card {
                position: relative;
                overflow: hidden;
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 22px;
                background:
                    radial-gradient(circle at top right, rgba(91, 140, 255, 0.22), transparent 34%),
                    linear-gradient(180deg, rgba(35, 38, 53, 0.98), rgba(28, 31, 44, 0.98));
                box-shadow: var(--card-shadow);
                margin-bottom: 1rem;
            }

            .spotlight-label {
                color: #9bb2ff;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 0.74rem;
                font-weight: 700;
                margin-bottom: 0.8rem;
            }

            .spotlight-title {
                color: var(--text);
                font-size: 1.35rem;
                font-weight: 700;
                line-height: 1.2;
                margin-bottom: 0.35rem;
            }

            .spotlight-copy {
                color: var(--muted);
                font-size: 0.95rem;
                line-height: 1.5;
                margin-bottom: 1rem;
            }

            .spotlight-meta {
                display: flex;
                flex-wrap: wrap;
                gap: 0.55rem;
            }

            .meta-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
                border-radius: 999px;
                padding: 0.45rem 0.8rem;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(167, 176, 211, 0.12);
                color: var(--muted);
                font-size: 0.82rem;
                font-weight: 600;
            }

            .stat-band {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 12px;
                margin-bottom: 1rem;
            }

            .stat-band.compact {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .stat-tile {
                border-radius: 16px;
                border: 1px solid var(--border);
                background: rgba(255,255,255,0.04);
                padding: 14px 16px;
            }

            .stat-tile-label {
                color: var(--muted);
                font-size: 0.8rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 0.35rem;
            }

            .stat-tile-value {
                color: var(--text);
                font-size: 1.3rem;
                font-weight: 700;
                line-height: 1.1;
                margin-bottom: 0.25rem;
            }

            .stat-tile-copy {
                color: var(--muted);
                font-size: 0.84rem;
                line-height: 1.35;
            }

            .session-shell {
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 20px;
                background:
                    linear-gradient(180deg, rgba(35, 38, 53, 0.98), rgba(28, 31, 44, 0.98));
                box-shadow: var(--card-shadow);
                margin-bottom: 1rem;
            }

            .session-topline {
                display: flex;
                justify-content: space-between;
                gap: 1rem;
                align-items: flex-start;
                margin-bottom: 0.8rem;
            }

            .session-title {
                color: var(--text);
                font-size: 1.18rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }

            .session-copy {
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.5;
                margin-bottom: 0;
            }

            .session-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 12px;
                margin-top: 1rem;
            }

            .session-cell {
                border-radius: 16px;
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(167, 176, 211, 0.08);
                padding: 12px 14px;
            }

            .session-cell-label {
                color: var(--muted);
                font-size: 0.78rem;
                font-weight: 600;
                margin-bottom: 0.2rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            .session-cell-value {
                color: var(--text);
                font-size: 0.95rem;
                line-height: 1.4;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(current_page: str) -> None:
    st.sidebar.markdown("## Implantar")
    nav_items = [
        ("dashboard", "Dashboard", "[D]", "Home.py"),
        ("sessions", "Sessoes", "[S]", "pages/1_Sessions.py"),
        ("detail", "Analises", "[A]", "pages/2_Session_Detail.py"),
        ("archived", "Arquivadas", "[R]", "pages/4_Archived_Sessions.py"),
        ("settings", "Configuracoes", "[C]", "pages/3_Settings.py"),
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
    st.sidebar.caption("Configuracoes e operacao centralizadas no painel.")
    if st.session_state.get(AUTH_ACTOR_KEY):
        st.sidebar.caption(f"Conectado como {st.session_state[AUTH_ACTOR_KEY]}")
    render_logout_control()


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
    elif normalized == "archived":
        css_class = "warning"
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
        response = client.get(f"{API_BASE}{path}", headers=_admin_headers())
        response.raise_for_status()
        return response.json()


def api_post(path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    with httpx.Client(timeout=60.0) as client:
        response = client.post(f"{API_BASE}{path}", json=payload or {}, headers=_admin_headers())
        response.raise_for_status()
        return response.json()


def api_put(path: str, payload: Dict[str, Any]) -> Any:
    with httpx.Client(timeout=60.0) as client:
        response = client.put(f"{API_BASE}{path}", json=payload, headers=_admin_headers())
        response.raise_for_status()
        return response.json()


def api_patch(path: str, payload: Dict[str, Any]) -> Any:
    with httpx.Client(timeout=60.0) as client:
        response = client.patch(f"{API_BASE}{path}", json=payload, headers=_admin_headers())
        response.raise_for_status()
        return response.json()


def api_delete(path: str) -> Any:
    with httpx.Client(timeout=30.0) as client:
        response = client.delete(f"{API_BASE}{path}", headers=_admin_headers())
        response.raise_for_status()
        return response.json() if response.content else None


def api_get_bytes(path: str) -> bytes:
    with httpx.Client(timeout=60.0) as client:
        response = client.get(f"{API_BASE}{path}", headers=_admin_headers())
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
                    <div class="row-title">{html.escape(str(row["score_type"]).replace("_", " ").title())}</div>
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
                    <div>Status</div>
                </div>
                {''.join(row_html)}
            </div>
        </body>
    </html>
    """

    row_count = max(len(items), 1)
    components.html(table_markup, height=96 + (row_count * 96), scrolling=False)


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


def render_spotlight_card(label: str, title: str, body: str, chips: Iterable[str]) -> None:
    chip_markup = "".join(f'<span class="meta-chip">{html.escape(chip)}</span>' for chip in chips if chip)
    st.markdown(
        f"""
        <div class="spotlight-card">
            <div class="spotlight-label">{html.escape(label)}</div>
            <div class="spotlight-title">{html.escape(title)}</div>
            <div class="spotlight-copy">{html.escape(body)}</div>
            <div class="spotlight-meta">{chip_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_band(items: Iterable[Dict[str, str]], compact: bool = False) -> None:
    entries = list(items)
    if not entries:
        return
    column_template = "repeat(3, minmax(0, 1fr))" if compact else "repeat(4, minmax(0, 1fr))"
    markup = "".join(
        f"""
        <div class="stat-tile">
            <div class="stat-tile-label">{html.escape(item.get("label", ""))}</div>
            <div class="stat-tile-value">{html.escape(item.get("value", "-"))}</div>
            <div class="stat-tile-copy">{html.escape(item.get("copy", ""))}</div>
        </div>
        """
        for item in entries
    )
    row_count = 1 if len(entries) <= 4 else 2
    height = 108 if row_count == 1 else 204
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

                    .stat-band {{
                        display: grid;
                        grid-template-columns: {column_template};
                        gap: 12px;
                    }}

                    .stat-tile {{
                        border-radius: 16px;
                        border: 1px solid rgba(167, 176, 211, 0.12);
                        background: rgba(255,255,255,0.04);
                        padding: 14px 16px;
                        min-height: 86px;
                        box-sizing: border-box;
                    }}

                    .stat-tile-label {{
                        color: #a6acc9;
                        font-size: 0.8rem;
                        font-weight: 600;
                        text-transform: uppercase;
                        letter-spacing: 0.05em;
                        margin-bottom: 0.35rem;
                    }}

                    .stat-tile-value {{
                        color: #f2f4fb;
                        font-size: 1.3rem;
                        font-weight: 700;
                        line-height: 1.1;
                        margin-bottom: 0.25rem;
                    }}

                    .stat-tile-copy {{
                        color: #a6acc9;
                        font-size: 0.84rem;
                        line-height: 1.35;
                    }}
                </style>
            </head>
            <body>
                <div class="stat-band">{markup}</div>
            </body>
        </html>
        """,
        height=height,
        scrolling=False,
    )


def render_session_card(
    title: str,
    description: str,
    status_html: str,
    chips: Iterable[str],
    facts: Iterable[tuple[str, str]],
) -> None:
    chip_markup = "".join(f'<span class="meta-chip">{html.escape(chip)}</span>' for chip in chips if chip)
    facts_markup = "".join(
        f"""
        <div class="session-cell">
            <div class="session-cell-label">{html.escape(label)}</div>
            <div class="session-cell-value">{html.escape(value)}</div>
        </div>
        """
        for label, value in facts
    )
    st.markdown(
        f"""
        <div class="session-shell">
            <div class="session-topline">
                <div>
                    <div class="session-title">{html.escape(title)}</div>
                    <p class="session-copy">{html.escape(description)}</p>
                </div>
                <div>{status_html}</div>
            </div>
            <div class="spotlight-meta">{chip_markup}</div>
            <div class="session-grid">{facts_markup}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
