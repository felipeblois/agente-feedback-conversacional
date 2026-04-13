import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_operational_health_exposes_http_metrics(async_client: AsyncClient):
    dashboard_response = await async_client.get("/api/v1/sessions/dashboard/summary")
    assert dashboard_response.status_code == 200

    health_response = await async_client.get("/health/operational")
    assert health_response.status_code == 200

    payload = health_response.json()
    assert payload["status"] == "ok"
    assert payload["uptime_seconds"] >= 0
    assert "http" in payload
    assert "llm" in payload
    assert payload["http"]["total_routes"] >= 1
    assert any(route["key"] == "GET /api/v1/sessions/dashboard/summary" for route in payload["http"]["routes"])
