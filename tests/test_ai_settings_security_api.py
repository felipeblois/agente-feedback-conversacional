import pytest
from app.services.llm_client import _pick_model_for_provider


@pytest.mark.asyncio
async def test_ai_test_endpoint_does_not_leak_sensitive_error_details(async_client, monkeypatch):
    async def fake_test_provider_connection(*args, **kwargs):
        raise RuntimeError("invalid api key sk-secret-123 gemini-secret-456")

    monkeypatch.setattr(
        "app.api.routes.settings.test_provider_connection",
        fake_test_provider_connection,
    )

    response = await async_client.post(
        "/api/v1/settings/ai/test",
        json={"provider": "gemini", "model": "gemini-2.5-flash"},
    )

    assert response.status_code == 500
    payload = response.json()
    assert payload["detail"] == "Nao foi possivel validar a conexao com o provedor agora."
    assert "secret" not in payload["detail"].lower()


@pytest.mark.asyncio
async def test_ai_test_endpoint_supports_openai_provider(async_client, monkeypatch):
    async def fake_test_provider_connection(*args, **kwargs):
        return {
            "success": True,
            "provider": "openai",
            "model": "gpt-4.1-mini",
            "credential_source": "platform",
            "message": "Conexao validada com sucesso.",
        }

    monkeypatch.setattr(
        "app.api.routes.settings.test_provider_connection",
        fake_test_provider_connection,
    )

    response = await async_client.post(
        "/api/v1/settings/ai/test",
        json={"provider": "openai", "model": "gpt-4.1-mini"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["success"] is True


def test_pick_model_for_selected_openai_provider_does_not_reuse_gemini_model():
    runtime_config = {
        "default_provider": "gemini",
        "default_model": "gemini-2.5-flash",
        "fallback_provider": "anthropic",
        "fallback_model": "claude-3-5-haiku-20241022",
    }

    assert _pick_model_for_provider("openai", runtime_config) == "gpt-4.1-mini"
