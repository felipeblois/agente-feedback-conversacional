import pytest
from httpx import AsyncClient


def build_session_payload(title: str = "Sessao exportacao", max_followup_questions: int = 1):
    return {
        "title": title,
        "description": "Sessao criada para testar exportacoes.",
        "score_type": "treinamento",
        "theme_summary": "Exportacoes operacionais",
        "session_goal": "Garantir consistencia de csv e pdf",
        "target_audience": "Analistas",
        "topics_to_explore": "Clareza, aplicabilidade e sintese",
        "ai_guidance": "Perguntas curtas",
        "is_anonymous": True,
        "max_followup_questions": max_followup_questions,
    }


@pytest.mark.asyncio
async def test_csv_and_pdf_exports_cover_happy_path(async_client: AsyncClient, monkeypatch):
    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload())
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    async def fake_conversation_llm(*args, **kwargs):
        return None

    async def fake_analysis_llm(*args, **kwargs):
        return (
            '{"summary":"Resumo de teste","positives":["Clareza"],'
            '"negatives":["Poucos exemplos"],"recommendations":["Adicionar casos práticos"]}'
        )

    monkeypatch.setattr("app.services.conversation_service.call_llm", fake_conversation_llm)
    monkeypatch.setattr("app.services.analysis_service.call_llm", fake_analysis_llm)

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True},
        )
        assert start_response.status_code == 200
        response_id = start_response.json()["response_id"]

        score_response = await async_client.post(
            f"/api/v1/public/{token}/score",
            json={"response_id": response_id, "score": 8},
        )
        assert score_response.status_code == 200
        assert score_response.json()["conversation_finished"] is False

        message_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Gostei da clareza, mas faltaram exemplos praticos."},
        )
        assert message_response.status_code == 200
        assert message_response.json()["conversation_finished"] is True

        csv_response = await async_client.get(f"/api/v1/sessions/{session_id}/export/csv")
        assert csv_response.status_code == 200
        assert csv_response.headers["content-type"].startswith("text/csv")
        csv_text = csv_response.text
        assert "response_id" in csv_text
        assert "Gostei da clareza" in csv_text

        analysis_response = await async_client.post(
            f"/api/v1/sessions/{session_id}/analyze",
            json={"provider": "gemini"},
        )
        assert analysis_response.status_code == 200
        assert analysis_response.json()["summary"] == "Resumo de teste"

        pdf_response = await async_client.get(f"/api/v1/sessions/{session_id}/export/pdf")
        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert pdf_response.content.startswith(b"%PDF")
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_exports_return_404_when_session_has_no_exportable_content(async_client: AsyncClient):
    create_response = await async_client.post(
        "/api/v1/sessions",
        json=build_session_payload(title="Sessao vazia"),
    )
    assert create_response.status_code == 201
    session_id = create_response.json()["id"]

    try:
        csv_response = await async_client.get(f"/api/v1/sessions/{session_id}/export/csv")
        assert csv_response.status_code == 404
        assert csv_response.json()["detail"] == "No data to export"

        pdf_response = await async_client.get(f"/api/v1/sessions/{session_id}/export/pdf")
        assert pdf_response.status_code == 404
        assert pdf_response.json()["detail"] == "Could not generate PDF"
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")


@pytest.mark.asyncio
async def test_pdf_export_keeps_only_two_latest_files_per_session(async_client: AsyncClient, monkeypatch, tmp_path):
    from app.services.export_service import export_service

    monkeypatch.setattr(export_service, "export_dir", tmp_path)
    export_service.export_dir.mkdir(parents=True, exist_ok=True)

    create_response = await async_client.post("/api/v1/sessions", json=build_session_payload(title="Sessao retencao"))
    assert create_response.status_code == 201
    created = create_response.json()
    session_id = created["id"]
    token = created["public_token"]

    async def fake_conversation_llm(*args, **kwargs):
        return None

    async def fake_analysis_llm(*args, **kwargs):
        return (
            '{"summary":"Resumo de retencao","positives":["Clareza"],'
            '"negatives":["Poucos exemplos"],"recommendations":["Adicionar casos praticos"]}'
        )

    monkeypatch.setattr("app.services.conversation_service.call_llm", fake_conversation_llm)
    monkeypatch.setattr("app.services.analysis_service.call_llm", fake_analysis_llm)

    try:
        start_response = await async_client.post(
            f"/api/v1/public/{token}/start",
            json={"anonymous": True},
        )
        assert start_response.status_code == 200
        response_id = start_response.json()["response_id"]

        score_response = await async_client.post(
            f"/api/v1/public/{token}/score",
            json={"response_id": response_id, "score": 9},
        )
        assert score_response.status_code == 200

        message_response = await async_client.post(
            f"/api/v1/public/{token}/message",
            json={"response_id": response_id, "message": "Sessao com bom aproveitamento geral."},
        )
        assert message_response.status_code == 200

        analysis_response = await async_client.post(
            f"/api/v1/sessions/{session_id}/analyze",
            json={"provider": "gemini"},
        )
        assert analysis_response.status_code == 200

        for _ in range(3):
            pdf_response = await async_client.get(f"/api/v1/sessions/{session_id}/export/pdf")
            assert pdf_response.status_code == 200
            assert pdf_response.content.startswith(b"%PDF")

        pdf_files = sorted(tmp_path.glob(f"session_{session_id}_report_*.pdf"))
        assert len(pdf_files) == 2
    finally:
        await async_client.delete(f"/api/v1/sessions/{session_id}")
