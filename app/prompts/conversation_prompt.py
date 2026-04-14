from app.models.session import Session


def build_conversation_system_prompt() -> str:
    return (
        "Voce e um entrevistador de feedback pos-evento para um produto SaaS. "
        "Sua funcao e conduzir uma conversa curta, objetiva, respeitosa e altamente aderente ao briefing da sessao. "
        "Voce deve decidir entre fazer apenas UMA proxima pergunta ou encerrar a conversa. "
        "Retorne APENAS um JSON valido no formato "
        '{"next_question":"texto da pergunta ou vazio","should_finish":true|false,"reason":"motivo_curto"}'
        ". "
        "A pergunta deve ter apenas uma intencao, soar natural, evitar repeticao e caber em ate 220 caracteres. "
        "Nao invente fatos que nao estejam no briefing ou no historico. "
        "Nao use markdown, bullets, comentarios extras, prefacios, nem texto fora do JSON. "
        "Se o participante respondeu pouco, priorize uma pergunta simples de clarificacao. "
        "Se ja houver contexto suficiente e a conversa estiver madura, use should_finish=true."
    )


def build_conversation_prompt(
    session: Session,
    score: int,
    system_questions_asked: int,
    max_questions: int,
    history_text: str,
    participant_answers_count: int = 0,
    participant_signal_strength: str = "medium",
    score_segment: str = "neutral",
) -> str:
    questions_remaining = max(max_questions - system_questions_asked, 0)
    briefing_parts = [
        f"Tipo de feedback: {session.score_type}",
        f"Titulo da sessao: {session.title}",
        f"Descricao geral: {session.description or '-'}",
        f"Tema principal: {session.theme_summary or '-'}",
        f"Objetivo da sessao: {session.session_goal or '-'}",
        f"Publico-alvo: {session.target_audience or '-'}",
        f"Topicos para explorar: {session.topics_to_explore or '-'}",
        f"Orientacoes extras para IA: {session.ai_guidance or '-'}",
    ]

    return (
        "Contexto da sessao:\n"
        + "\n".join(briefing_parts)
        + "\n\n"
        + "Regras operacionais:\n"
        + f"- Nota do participante: {score}\n"
        + f"- Segmento da nota: {score_segment}\n"
        + f"- Perguntas de aprofundamento ja feitas: {system_questions_asked}\n"
        + f"- Limite maximo de perguntas de aprofundamento: {max_questions}\n"
        + f"- Perguntas restantes possiveis: {questions_remaining}\n"
        + f"- Respostas textuais do participante: {participant_answers_count}\n"
        + f"- Sinal atual de contexto: {participant_signal_strength}\n"
        + "- Antes de encerrar por contexto suficiente, garanta pelo menos 2 perguntas de aprofundamento, exceto quando o limite total for menor que 2.\n"
        + "- Se o sinal atual estiver fraco ou a ultima resposta estiver muito curta, prefira uma pergunta de clarificacao pratica.\n"
        + "- Se ja houver contexto suficiente ou o limite tiver sido atingido, responda com should_finish=true.\n"
        + "- Se ainda fizer sentido aprofundar, responda com should_finish=false e gere apenas a proxima pergunta.\n"
        + "- A pergunta deve ter no maximo 220 caracteres.\n"
        + "- A pergunta deve ser aderente ao briefing e ao historico da conversa.\n"
        + "- Prefira perguntas conectadas ao objetivo, tema, publico ou topicos do briefing.\n"
        + "- Evite perguntas genericas como 'pode explicar melhor?' sem contexto.\n"
        + "- Evite repeticoes, generalidades vazias e perguntas duplas.\n\n"
        + "Historico da conversa:\n"
        + (history_text or "Sem historico alem da nota inicial.")
    )
