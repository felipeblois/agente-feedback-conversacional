import streamlit as st

from ui import (
    AUTH_ACTOR_KEY,
    api_delete,
    api_get,
    api_patch,
    api_post,
    api_put,
    configure_page,
    ensure_admin_access,
    format_dt,
    panel_header,
    render_sidebar,
)


def friendly_error(message: str) -> str:
    lowered = (message or "").lower()
    if "401" in lowered or "authentication required" in lowered or "invalid admin credentials" in lowered:
        return "Sua sessao administrativa nao esta valida. Entre novamente no painel."
    if "409" in lowered or "already exists" in lowered:
        return "Ja existe um admin com esse usuario."
    if "password must have at least" in lowered:
        return "A senha precisa ter pelo menos 4 caracteres."
    if "cannot delete your own admin user" in lowered:
        return "Voce nao pode excluir o proprio usuario admin conectado."
    if "not found" in lowered:
        return "O recurso solicitado nao foi encontrado."
    return "Nao foi possivel concluir essa acao agora. Revise os dados e tente novamente."


def render_friendly_error(exc: Exception) -> None:
    st.error(friendly_error(str(exc)))
    with st.expander("Detalhe tecnico", expanded=False):
        st.caption(f"{exc.__class__.__name__}: detalhe sensivel ocultado")


configure_page("Configuracoes", "C")
ensure_admin_access()
render_sidebar("settings")

panel_header(
    "Configuracoes",
    "Governanca da instancia InsightFlow",
    "Gerencie seguranca, credenciais, admins nominais e rastreabilidade operacional.",
)

try:
    config = api_get("/settings/ai")
    security_meta = api_get("/settings/admin/meta")
    admin_users = api_get("/settings/admin/users")
except Exception as exc:
    render_friendly_error(exc)
    st.stop()

provider_options = {
    "gemini": "Gemini",
    "openai": "OpenAI",
    "anthropic": "Claude",
    "fallback": "Jarvis",
}

provider_models = {
    "gemini": ["gemini-2.5-flash"],
    "openai": ["gpt-4.1-mini"],
    "anthropic": ["claude-3-5-haiku-20241022"],
    "fallback": ["auto"],
}

saved_default_provider = config.get("default_provider", "gemini")
saved_default_model = config.get("default_model", "gemini-2.5-flash")
saved_fallback_provider = config.get("fallback_provider", "fallback")
saved_fallback_model = config.get("fallback_model", "")

col_form, col_test = st.columns([1.45, 1])

with col_form:
    st.markdown("### Configuracao principal")
    with st.form("ai_settings_form"):
        customer_name = st.text_input("Nome do cliente", value=config.get("customer_name", ""))
        default_provider = st.selectbox(
            "Motor principal:",
            options=list(provider_options.keys()),
            index=list(provider_options.keys()).index(saved_default_provider),
            format_func=lambda key: provider_options[key],
        )
        default_model_options = provider_models[default_provider]
        default_model_index = (
            default_model_options.index(saved_default_model)
            if default_provider == saved_default_provider and saved_default_model in default_model_options
            else 0
        )
        default_model = st.selectbox(
            "Modelo principal",
            options=default_model_options,
            index=default_model_index,
        )
        fallback_provider = st.selectbox(
            "Motor de fallback:",
            options=list(provider_options.keys()),
            index=list(provider_options.keys()).index(saved_fallback_provider),
            format_func=lambda key: provider_options[key],
        )
        if fallback_provider == "fallback":
            st.text_input("Modelo de fallback", value="", disabled=True, placeholder="")
            fallback_model = ""
        else:
            fallback_model_options = provider_models[fallback_provider]
            fallback_model_index = (
                fallback_model_options.index(saved_fallback_model)
                if fallback_provider == saved_fallback_provider and saved_fallback_model in fallback_model_options
                else 0
            )
            fallback_model = st.selectbox(
                "Modelo de fallback",
                options=fallback_model_options,
                index=fallback_model_index,
            )
        gemini_api_key = st.text_input(
            "Gemini API Key",
            value="",
            type="password",
            placeholder=config.get("gemini_key_masked") or "Nenhuma chave salva",
        )
        openai_api_key = st.text_input(
            "OpenAI API Key",
            value="",
            type="password",
            placeholder=config.get("openai_key_masked") or "Nenhuma chave salva",
        )
        anthropic_api_key = st.text_input(
            "Anthropic API Key",
            value="",
            type="password",
            placeholder=config.get("anthropic_key_masked") or "Nenhuma chave salva",
        )
        clear_gemini = st.checkbox("Remover chave Gemini salva")
        clear_openai = st.checkbox("Remover chave OpenAI salva")
        clear_anthropic = st.checkbox("Remover chave Anthropic salva")
        notes = st.text_area("Observacoes", value=config.get("notes", ""))
        platform_fallback = st.checkbox(
            "Permitir fallback para credenciais da plataforma quando faltar chave do cliente",
            value=config.get("enable_platform_fallback", True),
        )

        submitted = st.form_submit_button("Salvar configuracoes", use_container_width=True)
        if submitted:
            try:
                payload = {
                    "credential_mode": config.get("credential_mode", "platform"),
                    "customer_name": customer_name,
                    "default_provider": default_provider,
                    "default_model": default_model,
                    "fallback_provider": fallback_provider,
                    "fallback_model": fallback_model,
                    "enable_platform_fallback": platform_fallback,
                    "notes": notes,
                    "gemini_api_key": gemini_api_key if gemini_api_key else None,
                    "openai_api_key": openai_api_key if openai_api_key else None,
                    "anthropic_api_key": anthropic_api_key if anthropic_api_key else None,
                    "clear_gemini_api_key": clear_gemini,
                    "clear_openai_api_key": clear_openai,
                    "clear_anthropic_api_key": clear_anthropic,
                }
                api_put("/settings/ai", payload)
                st.success("Configuracoes salvas com sucesso.")
                st.rerun()
            except Exception as exc:
                render_friendly_error(exc)

with col_test:
    st.markdown("### Estado atual")
    st.info(
        f"Principal: {provider_options.get(config['default_provider'], config['default_provider'])}\n\n"
        f"Fallback: {provider_options.get(config['fallback_provider'], config['fallback_provider'])}\n\n"
        f"Gemini configurado: {'Sim' if config['gemini_key_configured'] else 'Nao'}\n\n"
        f"OpenAI configurado: {'Sim' if config['openai_key_configured'] else 'Nao'}\n\n"
        f"Anthropic configurado: {'Sim' if config['anthropic_key_configured'] else 'Nao'}"
    )
    if security_meta.get("uses_default_password"):
        st.warning("O bootstrap ainda usa uma senha simples. Ajuste ADMIN_PASSWORD no .env antes do uso com cliente.")

    st.markdown("### Testar conexao")
    if st.button("Testar Gemini", use_container_width=True):
        try:
            result = api_post("/settings/ai/test", {"provider": "gemini", "model": "gemini-2.5-flash"})
            st.success(result["message"]) if result["success"] else st.warning(result["message"])
        except Exception as exc:
            render_friendly_error(exc)

    if st.button("Testar OpenAI", use_container_width=True):
        try:
            result = api_post(
                "/settings/ai/test",
                {"provider": "openai", "model": "gpt-4.1-mini"},
            )
            st.success(result["message"]) if result["success"] else st.warning(result["message"])
        except Exception as exc:
            render_friendly_error(exc)

    if st.button("Testar Claude 3.5 Haiku", use_container_width=True):
        try:
            result = api_post(
                "/settings/ai/test",
                {"provider": "anthropic", "model": "claude-3-5-haiku-20241022"},
            )
            st.success(result["message"]) if result["success"] else st.warning(result["message"])
        except Exception as exc:
            render_friendly_error(exc)

st.markdown("### Usuarios admin")
admin_col, list_col = st.columns([1.05, 1.55])

with admin_col:
    st.markdown("#### Novo admin nominal")
    with st.form("create_admin_user_form", clear_on_submit=True):
        username = st.text_input("Novo usuario admin")
        full_name = st.text_input("Nome nominal")
        password = st.text_input("Senha inicial", type="password")
        submitted = st.form_submit_button("Adicionar admin", use_container_width=True)
        if submitted:
            try:
                api_post(
                    "/settings/admin/users",
                    {
                        "username": username,
                        "full_name": full_name,
                        "password": password,
                    },
                )
                st.success("Usuario admin criado com sucesso.")
                st.rerun()
            except Exception as exc:
                render_friendly_error(exc)

with list_col:
    st.markdown("#### Admins cadastrados")
    current_actor = st.session_state.get(AUTH_ACTOR_KEY)
    if admin_users.get("items"):
        for item in admin_users["items"]:
            delete_confirm_key = f"delete_target_admin_id_{item['id']}"
            with st.container(border=True):
                status_text = "Ativo" if item.get("is_active") else "Desativado"
                st.markdown(
                    f"**{item['username']}** | {item.get('full_name') or 'Sem nome nominal'} | {status_text}"
                )
                st.caption(
                    f"Criado por {item.get('created_by') or 'bootstrap'} em {format_dt(item['created_at'])}"
                )
                action_cols = st.columns([1, 1, 1.45, 1])
                with action_cols[0]:
                    toggle_label = "Desativar" if item.get("is_active") else "Reativar"
                    if st.button(toggle_label, key=f"toggle-admin-{item['id']}", use_container_width=True):
                        try:
                            api_patch(
                                f"/settings/admin/users/{item['id']}",
                                {
                                    "full_name": item.get("full_name") or "",
                                    "is_active": not item.get("is_active"),
                                },
                            )
                            st.success("Status do admin atualizado.")
                            st.rerun()
                        except Exception as exc:
                            render_friendly_error(exc)
                with action_cols[1]:
                    if st.button("Nova senha", key=f"password-admin-{item['id']}", use_container_width=True):
                        st.session_state["password_target_admin_id"] = item["id"]
                        st.session_state.pop("delete_target_admin_id", None)
                        st.rerun()
                with action_cols[2]:
                    if st.session_state.get("password_target_admin_id") == item["id"]:
                        st.caption(f"Atualizar senha de {item['username']}")
                        with st.form(f"password-form-{item['id']}"):
                            new_password = st.text_input(
                                "Nova senha",
                                type="password",
                                key=f"new-password-{item['id']}",
                            )
                            save_password = st.form_submit_button(
                                "Salvar senha",
                                use_container_width=True,
                            )
                            if save_password:
                                try:
                                    api_post(
                                        f"/settings/admin/users/{item['id']}/password",
                                        {"password": new_password},
                                    )
                                    st.session_state.pop("password_target_admin_id", None)
                                    st.success("Senha atualizada com sucesso.")
                                    st.rerun()
                                except Exception as exc:
                                    render_friendly_error(exc)
                with action_cols[3]:
                    disable_delete = item["username"] == current_actor
                    if st.button(
                        "Excluir",
                        key=f"delete-admin-{item['id']}",
                        use_container_width=True,
                        disabled=disable_delete,
                    ):
                        st.session_state["delete_target_admin_id"] = item["id"]
                        st.session_state.pop("password_target_admin_id", None)
                        st.rerun()
                    if disable_delete:
                        st.caption("Usuario conectado")

                if st.session_state.get("delete_target_admin_id") == item["id"]:
                    st.warning(
                        "Essa acao remove o admin nominal do cadastro. O historico de autoria das sessoes sera preservado."
                    )
                    delete_cols = st.columns([1, 1, 2.2])
                    with delete_cols[0]:
                        if st.button(
                            "Confirmar exclusao",
                            key=f"confirm-delete-admin-{item['id']}",
                            use_container_width=True,
                        ):
                            try:
                                api_delete(f"/settings/admin/users/{item['id']}")
                                st.session_state.pop("delete_target_admin_id", None)
                                st.success("Usuario admin excluido com sucesso.")
                                st.rerun()
                            except Exception as exc:
                                render_friendly_error(exc)
                    with delete_cols[1]:
                        if st.button(
                            "Cancelar",
                            key=f"cancel-delete-admin-{item['id']}",
                            use_container_width=True,
                        ):
                            st.session_state.pop("delete_target_admin_id", None)
                            st.rerun()
    else:
        st.caption("Nenhum usuario admin nominal cadastrado ainda. Use o bootstrap para criar o primeiro.")
