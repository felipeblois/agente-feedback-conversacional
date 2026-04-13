import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/sessions/dashboard/summary")
    assert response.status_code == 200
    payload = response.json()
    assert "total_sessions" in payload
    assert "recent_sessions" in payload


@pytest.mark.asyncio
async def test_settings_public_view_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/settings/ai")
    assert response.status_code == 200
    payload = response.json()
    assert "default_provider" in payload
    assert "fallback_provider" in payload
