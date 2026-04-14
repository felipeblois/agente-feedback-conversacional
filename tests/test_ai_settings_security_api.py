import pytest


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
