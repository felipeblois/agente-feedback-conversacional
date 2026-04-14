import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.participant import Participant


def build_session_payload(title: str = "Sessao privacidade"):
    return {
        "title": title,
        "description": "Sessao para validar privacidade e retencao.",
        "score_type": "treinamento",
        "theme_summary": "Privacidade operacional",
        "session_goal": "Garantir exportacao e anonimato",
        "target_audience": "Equipe piloto",
        "topics_to_explore": "Consentimento, anonimato, exclusao",
        "ai_guidance": "Perguntas diretas",
        "is_anonymous": True,
        "max_followup_questions": 2,
    }


@pytest.mark.asyncio
async def test_session_privacy_summary_exposes_retention_policy(async_client: AsyncClient):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload())
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    try:
        summary_response = await async_client.get(f"/api/v1/sessions/{session_id}/privacy/summary")
        assert summary_response.status_code == 200
        payload = summary_response.json()
        assert payload["session_id"] == session_id
        assert "retention_policy" in payload
        assert payload["retention_policy"]["responses_days"] >= 1
        assert "Anonimizar participante" in payload["participant_anonymization_scope"]
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_participant_export_and_anonymization(async_client: AsyncClient, db_session, monkeypatch):
    create_response = await async_client.post(
        "/api/v1/sessions",
        json=build_session_payload("Sessao exportacao participante"),
    )
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    async def fake_call_llm(*args, **kwargs):
        return None

    monkeypatch.setattr("app.services.conversation_service.call_llm", fake_call_llm)

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={
                "participant_name": "Pessoa Teste",
                "participant_email": "pessoa@example.com",
                "anonymous": False,
                "consent_accepted": True,
            },
        )
        assert start_response.status_code == 200
        response_id = start_response.json()["response_id"]

        score_response = await async_client.post(
            f"/api/v1/public/{token}/score",
            json={"response_id": response_id, "score": 7},
        )
        assert score_response.status_code == 200

        message_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Achei o conteudo util, mas pode melhorar."},
        )
        assert message_response.status_code == 200

        participant_result = await db_session.execute(
            select(Participant).where(Participant.session_id == session_id)
        )
        participant = participant_result.scalar_one()

        export_response = await async_client.get(
            f"/api/v1/sessions/{session_id}/participants/{participant.id}/export"
        )
        assert export_response.status_code == 200
        export_payload = export_response.json()
        assert export_payload["participant_name"] == "Pessoa Teste"
        assert export_payload["participant_email"] == "pessoa@example.com"
        assert export_payload["responses"]
        assert export_payload["responses"][0]["messages"]

        anonymize_response = await async_client.delete(
            f"/api/v1/sessions/{session_id}/participants/{participant.id}"
        )
        assert anonymize_response.status_code == 200
        anonymize_payload = anonymize_response.json()
        assert anonymize_payload["anonymous"] is True
        assert anonymize_payload["removed_identifiers"] is True

        await db_session.refresh(participant)
        assert participant.name is None
        assert participant.email is None
        assert participant.anonymous is True
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")
