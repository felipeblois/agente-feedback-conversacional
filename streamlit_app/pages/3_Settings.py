import streamlit as st

from ui import (
    api_get,
    api_post,
    api_put,
    configure_page,
    panel_header,
    render_sidebar,
)


configure_page("Configuracoes", "⚙")
render_sidebar("settings")

panel_header(
    "Configuracoes",
    "Credenciais de IA",
    "Defina se esta instancia usa as chaves do cliente ou as credenciais padrao da plataforma.",
)

try:
    config = api_get("/settings/ai")
except Exception as exc:
    st.error(f"Nao foi possivel carregar as configuracoes: {exc}")
    st.stop()

mode_options = {
    "platform": "Usar credenciais da plataforma",
    "customer": "Usar credenciais do cliente",
}

col_form, col_test = st.columns([1.5, 1])

with col_form:
    st.markdown("### Configuracao principal")
    with st.form("ai_settings_form"):
        mode = st.radio(
            "Origem das credenciais",
            options=list(mode_options.keys()),
            index=list(mode_options.keys()).index(config["credential_mode"]),
            format_func=lambda key: mode_options[key],
        )
        customer_name = st.text_input("Nome do cliente", value=config.get("customer_name", ""))
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value="",
            type="password",
            placeholder=config.get("gemini_key_masked") or "Nenhuma chave salva",
        )
        anthropic_api_key = st.text_input(
            "Anthropic API Key",
            value="",
            type="password",
            placeholder=config.get("anthropic_key_masked") or "Nenhuma chave salva",
        )
        notes = st.text_area("Observacoes", value=config.get("notes", ""))

        submitted = st.form_submit_button("Salvar configuracoes", use_container_width=True)
        if submitted:
            try:
                payload = {
                    "credential_mode": mode,
                    "customer_name": customer_name,
                    "default_provider": "gemini",
                    "default_model": "gemini-2.5-flash",
                    "fallback_provider": "anthropic",
                    "fallback_model": "claude-3-5-haiku-20241022",
                    "enable_platform_fallback": True,
                    "notes": notes,
                    "gemini_api_key": gemini_api_key if gemini_api_key else None,
                    "anthropic_api_key": anthropic_api_key if anthropic_api_key else None,
                }
                api_put("/settings/ai", payload)
                st.success("Configuracoes salvas com sucesso.")
                st.rerun()
            except Exception as exc:
                st.error(f"Falha ao salvar configuracoes: {exc}")

with col_test:
    st.markdown("### Estado atual")
    st.info(
        f"Modo: {mode_options.get(config['credential_mode'], config['credential_mode'])}\n\n"
        f"Gemini configurado: {'Sim' if config['gemini_key_configured'] else 'Nao'}\n\n"
        f"Anthropic configurado: {'Sim' if config['anthropic_key_configured'] else 'Nao'}"
    )
    st.caption("As chaves ficam mascaradas na interface e nunca sao exibidas por completo.")

    st.markdown("### Testar conexao")
    if st.button("Testar Gemini", use_container_width=True):
        try:
            result = api_post("/settings/ai/test", {"provider": "gemini", "model": "gemini-2.5-flash"})
            if result["success"]:
                st.success(result["message"])
            else:
                st.warning(result["message"])
        except Exception as exc:
            st.error(f"Falha ao testar Gemini: {exc}")

    if st.button("Testar Claude 3.5 Haiku", use_container_width=True):
        try:
            result = api_post(
                "/settings/ai/test",
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
            )
            if result["success"]:
                st.success(result["message"])
            else:
                st.warning(result["message"])
        except Exception as exc:
            st.error(f"Falha ao testar Anthropic: {exc}")

    st.markdown("### Modelo comercial")
    st.markdown(
        "- `Credenciais do cliente`: usa as chaves salvas nesta tela.\n"
        "- `Credenciais da plataforma`: usa as chaves do `.env` da instancia.\n"
        "- Em ambos os casos, a aplicacao segue `Gemini -> Anthropic -> Jarvis`."
    )
