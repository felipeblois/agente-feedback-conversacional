import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.response import Response
from app.services.conversation_service import conversation_service


async def _create_session(async_client: AsyncClient, max_followup_questions: int = 3):
    response = await async_client.post(
        "/api/v1/sessions",
        json={
            "title": "Sessao teste Gemini",
            "description": "Sessao para validar fluxo publico",
            "score_type": "treinamento",
            "theme_summary": "Lideranca pratica",
            "session_goal": "Entender clareza e aplicabilidade",
            "target_audience": "Coordenadores",
            "topics_to_explore": "Exemplos praticos, clareza, aplicabilidade",
            "ai_guidance": "Fazer perguntas curtas e objetivas",
            "is_anonymous": True,
            "max_followup_questions": max_followup_questions,
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_public_flow_completes_with_llm_path(async_client: AsyncClient, monkeypatch):
    created = await _create_session(async_client, max_followup_questions=3)
    token = created["public_token"]
    session_id = created["id"]

    llm_answers = iter(
        [
            '{"next_question":"Qual parte do treinamento foi mais util para voce?","should_finish":false}',
            '{"next_question":"Que exemplo pratico mais ajudou voce a entender o conteudo?","should_finish":false}',
            '{"next_question":"","should_finish":true}',
        ]
    )

    async def fake_call_llm(*args, **kwargs):
        return next(llm_answers)

    monkeypatch.setattr("app.services.conversation_service.call_llm", fake_call_llm)

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert start_response.status_code == 200
        start_payload = start_response.json()
        assert start_payload["first_question"]["type"] == "score"

        response_id = start_payload["response_id"]

        score_response = await async_client.post(
            f"/api/v1/public/{token}/score",
            json={"response_id": response_id, "score": 9},
        )
        assert score_response.status_code == 200
        score_payload = score_response.json()
        assert score_payload["conversation_finished"] is False
        assert score_payload["next_question"]["text"] == "Qual parte do treinamento foi mais util para voce?"

        message_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Os exemplos praticos foram muito bons."},
        )
        assert message_response.status_code == 200
        message_payload = message_response.json()
        assert message_payload["conversation_finished"] is False
        assert "Que exemplo pratico" in message_payload["next_question"]["text"]

        finish_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Aplicarei isso na rotina da equipe."},
        )
        assert finish_response.status_code == 200
        finish_payload = finish_response.json()
        assert finish_payload["conversation_finished"] is True
        assert finish_payload["finish_reason"] == "llm_sufficient_context"
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_public_flow_uses_fallback_when_llm_fails(async_client: AsyncClient, monkeypatch):
    created = await _create_session(async_client, max_followup_questions=2)
    token = created["public_token"]
    session_id = created["id"]

    async def fake_call_llm(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.conversation_service.call_llm", fake_call_llm)

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        response_id = start_response.json()["response_id"]

        score_response = await async_client.post(
            f"/api/v1/public/{token}/score",
            json={"response_id": response_id, "score": 4},
        )
        score_payload = score_response.json()
        assert score_payload["conversation_finished"] is False
        assert score_payload["next_question"]["type"] == "text"
        assert score_payload["next_question"]["text"]

        message_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Faltaram exemplos reais."},
        )
        message_payload = message_response.json()
        assert message_payload["conversation_finished"] is False

        finish_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Tambem faltou aprofundar a pratica."},
        )
        finish_payload = finish_response.json()
        assert finish_payload["conversation_finished"] is True
        assert finish_payload["finish_reason"] == "max_questions_reached"
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


def test_minimum_required_questions_rule():
    assert conversation_service._minimum_required_questions(1) == 1
    assert conversation_service._minimum_required_questions(2) == 2
    assert conversation_service._minimum_required_questions(6) == 2


@pytest.mark.asyncio
async def test_finish_endpoint_marks_response_as_completed(async_client: AsyncClient, db_session):
    created = await _create_session(async_client, max_followup_questions=3)
    token = created["public_token"]
    session_id = created["id"]

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True, "consent_accepted": True},
        )
        assert start_response.status_code == 200
        response_id = start_response.json()["response_id"]

        finish_response = await async_client.post(
            f"/api/v1/public/{token}/finish",
            json={"response_id": response_id},
        )
        assert finish_response.status_code == 200
        assert finish_response.json() == {"status": "completed"}

        db_result = await db_session.execute(select(Response).where(Response.id == response_id))
        response = db_result.scalar_one()
        assert response.status == "completed"
        assert response.completed_at is not None
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")
