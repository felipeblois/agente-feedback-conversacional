import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.participant import Participant
from app.models.response import Response


def build_session_payload(title: str = "Sessao publica"):
    return {
        "title": title,
        "description": "Sessao para validar endpoints publicos.",
        "score_type": "palestra",
        "theme_summary": "Comunicacao e clareza",
        "session_goal": "Validar template e fluxo publico",
        "target_audience": "Lideres",
        "topics_to_explore": "Clareza, ritmo, exemplos",
        "ai_guidance": "Tom acolhedor e objetivo",
        "is_anonymous": True,
        "max_followup_questions": 2,
    }


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


@pytest.mark.asyncio
async def test_public_page_renders_for_active_session(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload())
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        page_response = await async_client.get(f"/f/{token}")
        assert page_response.status_code == 200
        assert "text/html" in page_response.headers["content-type"]
        assert "Sessao publica" in page_response.text
        assert "compartilhar minhas respostas" in page_response.text
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_page_returns_404_for_archived_session(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao arquivada"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        archive_response = await async_client.post(f"/api/v1/sessions/{session_id}/archive")
        assert archive_response.status_code == 200

        page_response = await async_client.get(f"/f/{token}")
        assert page_response.status_code == 404

        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert start_response.status_code == 404
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_start_persists_named_participant(async_client: AsyncClient, db_session):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao nominal"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={
                "participant_name": "Felipe Teste",
                "participant_email": "felipe@example.com",
                "anonymous": False,
                "consent_accepted": True,
            },
        )
        assert start_response.status_code == 200
        response_id = start_response.json()["response_id"]

        participant_result = await db_session.execute(
            select(Participant).where(Participant.session_id == session_id)
        )
        participant = participant_result.scalar_one()
        assert participant.name == "Felipe Teste"
        assert participant.email == "felipe@example.com"
        assert participant.anonymous is False

        response_result = await db_session.execute(select(Response).where(Response.id == response_id))
        response = response_result.scalar_one()
        assert response.participant_id == participant.id
        assert response.session_id == session_id
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_start_requires_consent(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao consentimento"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": False},
        )
        assert start_response.status_code == 400
        assert start_response.json()["detail"] == "Consentimento obrigatorio para iniciar o feedback."
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")
