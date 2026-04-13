import pytest
from httpx import AsyncClient


def build_session_payload(title: str = "Sessao integracao"):
    return {
        "title": title,
        "description": "Sessao criada pelos testes de integracao.",
        "score_type": "workshop",
        "theme_summary": "Aplicacao pratica",
        "session_goal": "Medir clareza e confianca de execucao",
        "target_audience": "Coordenadores",
        "topics_to_explore": "Clareza, dinamica, exemplos, aplicabilidade",
        "ai_guidance": "Perguntas curtas e objetivas",
        "is_anonymous": True,
        "max_followup_questions": 4,
    }


@pytest.mark.asyncio
async def test_session_detail_and_dashboard_contract(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload())
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]

    try:
        detail_response = await async_client.get(f"/api/v1/sessions/{session_id}/detail")
        assert detail_response.status_code == 200
        detail = detail_response.json()

        assert detail["id"] == session_id
        assert detail["title"] == "Sessao integracao"
        assert detail["status"] == "active"
        assert detail["public_url"].endswith(created["public_token"])
        assert "score_distribution" in detail
        assert "recent_responses" in detail
        assert "theme_summary" in detail
        assert detail["max_followup_questions"] == 4

        dashboard_response = await async_client.get("/api/v1/sessions/dashboard/summary")
        assert dashboard_response.status_code == 200
        dashboard = dashboard_response.json()

        assert "total_sessions" in dashboard
        assert "archived_sessions" in dashboard
        assert "recent_sessions" in dashboard
        assert any(item["id"] == session_id for item in dashboard["recent_sessions"])
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_session_endpoints_return_404_for_missing_session(async_client: AsyncClient):
    missing_id = 999999

    get_response = await async_client.get(f"/api/v1/sessions/{missing_id}")
    assert get_response.status_code == 404

    detail_response = await async_client.get(f"/api/v1/sessions/{missing_id}/detail")
    assert detail_response.status_code == 404

    patch_response = await async_client.patch(
        f"/api/v1/sessions/{missing_id}",
        json={"title": "Nao existe"},
    )
    assert patch_response.status_code == 404

    archive_response = await async_client.post(f"/api/v1/sessions/{missing_id}/archive")
    assert archive_response.status_code == 404

    reactivate_response = await async_client.post(f"/api/v1/sessions/{missing_id}/reactivate")
    assert reactivate_response.status_code == 404

    delete_response = await async_client.delete(f"/api/v1/sessions/{missing_id}")
    assert delete_response.status_code == 404
