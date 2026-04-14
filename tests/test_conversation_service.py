from app.services.conversation_service import conversation_service


def test_conversation_service_sanitizes_single_question():
    question = conversation_service._sanitize_question("  Qual foi o ponto mais util desta sessao??  ")
    assert question == "Qual foi o ponto mais util desta sessao?"
    assert conversation_service._is_valid_question(question) is True


def test_conversation_service_rejects_invalid_instructional_payload():
    question = conversation_service._sanitize_question("Retorne um json com sua resposta")
    assert conversation_service._is_valid_question(question) is False


def test_conversation_service_parses_json_payload():
    raw = 'texto irrelevante {"next_question":"Qual parte gerou mais valor para voce?","should_finish":false}'
    payload = conversation_service._parse_llm_payload(raw)
    assert payload["next_question"] == "Qual parte gerou mais valor para voce?"
    assert payload["should_finish"] is False


def test_conversation_service_minimum_required_questions_scales_with_depth():
    assert conversation_service._minimum_required_questions(1) == 1
    assert conversation_service._minimum_required_questions(2) == 1
    assert conversation_service._minimum_required_questions(4) == 2
    assert conversation_service._minimum_required_questions(8) == 3


def test_conversation_service_signal_strength_uses_answer_quality():
    assert conversation_service._signal_strength([]) == "weak"
    assert conversation_service._signal_strength(["bom"]) == "weak"
    assert conversation_service._signal_strength(["Foi claro e objetivo para mim"]) == "medium"
    assert (
        conversation_service._signal_strength(
            [
                "Gostei dos exemplos praticos e da organizacao do conteudo",
                "Vou aplicar isso na rotina com a equipe ainda esta semana",
            ]
        )
        == "strong"
    )
