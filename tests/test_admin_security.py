import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_endpoints_require_authentication(unauthenticated_async_client: AsyncClient):
    dashboard_response = await unauthenticated_async_client.get("/api/v1/sessions/dashboard/summary")
    assert dashboard_response.status_code == 401
    assert dashboard_response.json()["detail"] == "Admin authentication required"

    settings_response = await unauthenticated_async_client.get("/api/v1/settings/ai")
    assert settings_response.status_code == 401

    operational_health = await unauthenticated_async_client.get("/health/operational")
    assert operational_health.status_code == 401


@pytest.mark.asyncio
async def test_public_endpoints_remain_available_without_admin_auth(unauthenticated_async_client: AsyncClient):
    health_response = await unauthenticated_async_client.get("/health")
    assert health_response.status_code == 200

    create_response = await unauthenticated_async_client.post(
        "/api/v1/public/invalid-token/start",
        json={"anonymous": True},
    )
    assert create_response.status_code == 404


@pytest.mark.asyncio
async def test_settings_update_creates_audit_log(async_client: AsyncClient):
    update_response = await async_client.put(
        "/api/v1/settings/ai",
        json={
            "credential_mode": "platform",
            "customer_name": "Cliente teste",
            "default_provider": "gemini",
            "default_model": "gemini-2.5-flash",
            "fallback_provider": "anthropic",
            "fallback_model": "claude-3-5-haiku-20241022",
            "enable_platform_fallback": True,
            "notes": "Ajuste auditado pela suite",
            "clear_gemini_api_key": False,
            "clear_anthropic_api_key": False,
        },
    )
    assert update_response.status_code == 200

    audit_response = await async_client.get("/api/v1/settings/ai/audit")
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["items"]
    assert any("customer_name" in item["details"] or "notes" in item["details"] for item in payload["items"])


@pytest.mark.asyncio
async def test_admin_meta_exposes_instance_security_context(async_client: AsyncClient):
    response = await async_client.get("/api/v1/settings/admin/meta")
    assert response.status_code == 200
    payload = response.json()
    assert "instance_name" in payload
    assert "instance_id" in payload
    assert "admin_username" in payload
    assert "uses_default_password" in payload
