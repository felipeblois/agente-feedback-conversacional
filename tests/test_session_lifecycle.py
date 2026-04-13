import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_session_can_be_created_updated_archived_reactivated_and_deleted(async_client: AsyncClient):
    create_response = await async_client.post(
        "/api/v1/sessions",
        json={
            "title": "Sessao de ciclo",
            "description": "Criada para validar o ciclo administrativo.",
            "score_type": "workshop",
            "theme_summary": "Colaboracao pratica",
            "session_goal": "Medir clareza e aplicabilidade",
            "target_audience": "Gestores",
            "topics_to_explore": "Clareza, exemplos, dinamica",
            "ai_guidance": "Perguntas curtas",
            "is_anonymous": True,
            "max_followup_questions": 4,
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]

    patch_response = await async_client.patch(
        f"/api/v1/sessions/{session_id}",
        json={
            "title": "Sessao de ciclo atualizada",
            "session_goal": "Medir clareza, aplicabilidade e engajamento",
            "max_followup_questions": 6,
        },
    )
    assert patch_response.status_code == 200
    updated = patch_response.json()
    assert updated["title"] == "Sessao de ciclo atualizada"
    assert updated["session_goal"] == "Medir clareza, aplicabilidade e engajamento"
    assert updated["max_followup_questions"] == 6

    archive_response = await async_client.post(f"/api/v1/sessions/{session_id}/archive")
    assert archive_response.status_code == 200
    assert archive_response.json()["status"] == "archived"

    archived_list = await async_client.get("/api/v1/sessions?status=archived")
    assert archived_list.status_code == 200
    assert any(item["id"] == session_id for item in archived_list.json())

    reactivate_response = await async_client.post(f"/api/v1/sessions/{session_id}/reactivate")
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["status"] == "active"

    active_list = await async_client.get("/api/v1/sessions")
    assert active_list.status_code == 200
    assert any(item["id"] == session_id for item in active_list.json())

    delete_response = await async_client.delete(f"/api/v1/sessions/{session_id}")
    assert delete_response.status_code == 200
