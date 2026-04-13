import asyncio

import pytest

from app.core.observability import observability_service
from app.services.llm_client import call_llm


@pytest.mark.asyncio
async def test_llm_observability_records_provider_latency(db_session, monkeypatch):
    class FakeMessage:
        content = "CONECTADO"

    class FakeChoice:
        message = FakeMessage()

    class FakeResponse:
        choices = [FakeChoice()]

    async def fake_completion(*args, **kwargs):
        await asyncio.sleep(0)
        return FakeResponse()

    monkeypatch.setattr("app.services.llm_client.litellm.acompletion", fake_completion)

    result = await call_llm(
        db_session,
        "Diga CONECTADO",
        "Responda apenas CONECTADO.",
        provider_override="gemini",
        model_override="gemini-2.5-flash",
    )

    assert result == "CONECTADO"

    snapshot = observability_service.snapshot()
    assert snapshot["llm"]["total_models"] >= 1
    assert any(
        item["key"] == "gemini:gemini-2.5-flash:selected" and item["count"] == 1 and item["errors"] == 0
        for item in snapshot["llm"]["models"]
    )
