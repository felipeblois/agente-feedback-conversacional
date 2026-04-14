from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.core.public_access import public_access_service
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


@pytest.fixture(autouse=True)
def clear_public_access_limits():
    public_access_service._events.clear()
    yield
    public_access_service._events.clear()


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


@pytest.mark.asyncio
async def test_public_link_can_be_revoked(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao revogavel"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        revoke_response = await async_client.post(f"/api/v1/sessions/{session_id}/public-link/revoke")
        assert revoke_response.status_code == 200

        page_response = await async_client.get(f"/f/{token}")
        assert page_response.status_code == 410

        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert start_response.status_code == 410
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_link_can_expire(async_client: AsyncClient):
    expired_at = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    payload = build_session_payload("Sessao expirada")
    payload["public_link_expires_at"] = expired_at

    create_response = await async_client.post("/api/v1/sessions", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        page_response = await async_client.get(f"/f/{token}")
        assert page_response.status_code == 410
        assert page_response.json()["detail"] == "Link publico indisponivel."
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_start_blocks_honeypot(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao anti spam"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={
                "anonymous": True,
                "consent_accepted": True,
                "website": "https://spam.invalid",
            },
        )
        assert start_response.status_code == 400
        assert start_response.json()["detail"] == "Nao foi possivel iniciar o feedback."
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_start_rate_limit_returns_429(async_client: AsyncClient, monkeypatch):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao limitada"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    original_limits = dict(public_access_service._limits)
    monkeypatch.setattr(public_access_service, "_limits", {**original_limits, "start": (1, 300)})

    try:
        first_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert first_response.status_code == 200

        second_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert second_response.status_code == 429
        assert (
            second_response.json()["detail"]
            == "Limite temporario de tentativas atingido. Aguarde um instante e tente novamente."
        )
    finally:
        monkeypatch.setattr(public_access_service, "_limits", original_limits)
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_rotate_public_link_invalidates_previous_token(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload("Sessao rotativa"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    old_token = created["public_token"]

    try:
        rotate_response = await async_client.post(f"/api/v1/sessions/{session_id}/public-link/rotate")
        assert rotate_response.status_code == 200
        new_token = rotate_response.json()["public_token"]
        assert new_token != old_token

        old_page_response = await async_client.get(f"/f/{old_token}")
        assert old_page_response.status_code == 404

        new_page_response = await async_client.get(f"/f/{new_token}")
        assert new_page_response.status_code == 200
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")
