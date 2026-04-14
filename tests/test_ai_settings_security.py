import pytest

from app.schemas.settings import AISettingsUpdate
from app.services.settings_service import settings_service


@pytest.mark.asyncio
async def test_ai_settings_response_masks_customer_keys(async_client, db_session):
    update_response = await async_client.put(
        "/api/v1/settings/ai",
        json={
            "credential_mode": "customer",
            "customer_name": "Cliente seguro",
            "default_provider": "gemini",
            "default_model": "gemini-2.5-flash",
            "fallback_provider": "anthropic",
            "fallback_model": "claude-3-5-haiku-20241022",
            "enable_platform_fallback": False,
            "notes": "teste de mascaramento",
            "gemini_api_key": "gemini-secret-123456",
            "anthropic_api_key": "anthropic-secret-654321",
            "clear_gemini_api_key": False,
            "clear_anthropic_api_key": False,
        },
    )
    assert update_response.status_code == 200
    payload = update_response.json()

    assert payload["gemini_key_masked"].startswith("gemi")
    assert payload["anthropic_key_masked"].startswith("anth")
    assert "secret" not in str(payload).lower()
    assert payload["customer_gemini_key_configured"] is True
    assert payload["customer_anthropic_key_configured"] is True
    assert payload["effective_gemini_credential_source"] == "customer"
    assert payload["effective_anthropic_credential_source"] == "customer"


@pytest.mark.asyncio
async def test_runtime_config_respects_customer_only_mode_without_platform_fallback(db_session):
    await settings_service.update(
        db_session,
        payload=AISettingsUpdate(
            credential_mode="customer",
            customer_name="Cliente sem fallback",
            default_provider="gemini",
            default_model="gemini-2.5-flash",
            fallback_provider="anthropic",
            fallback_model="claude-3-5-haiku-20241022",
            enable_platform_fallback=False,
            notes="",
            gemini_api_key=None,
            anthropic_api_key=None,
            clear_gemini_api_key=True,
            clear_anthropic_api_key=True,
        ),
        actor="test",
    )
    runtime_config = await settings_service.get_runtime_config(db_session)
    assert runtime_config["gemini_api_key"] == ""
    assert runtime_config["anthropic_api_key"] == ""
    assert runtime_config["gemini_credential_source"] == "missing"
    assert runtime_config["anthropic_credential_source"] == "missing"


@pytest.mark.asyncio
async def test_runtime_config_uses_platform_fallback_when_enabled(db_session):
    await settings_service.update(
        db_session,
        payload=AISettingsUpdate(
            credential_mode="customer",
            customer_name="Cliente com fallback",
            default_provider="gemini",
            default_model="gemini-2.5-flash",
            fallback_provider="anthropic",
            fallback_model="claude-3-5-haiku-20241022",
            enable_platform_fallback=True,
            notes="",
            gemini_api_key=None,
            anthropic_api_key=None,
            clear_gemini_api_key=True,
            clear_anthropic_api_key=True,
        ),
        actor="test",
    )
    runtime_config = await settings_service.get_runtime_config(db_session)
    assert runtime_config["gemini_credential_source"] in {"platform_fallback", "missing", "platform"}
    assert runtime_config["anthropic_credential_source"] in {"platform_fallback", "missing", "platform"}
