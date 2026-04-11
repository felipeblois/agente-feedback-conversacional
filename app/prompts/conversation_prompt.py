from app.models.session import Session


def build_conversation_system_prompt() -> str:
    return (
        "Voce e um entrevistador de feedback pos-evento. "
        "Sua funcao e conduzir uma conversa curta, objetiva e contextualizada. "
        "Retorne APENAS um JSON valido com as chaves next_question e should_finish. "
        "A pergunta deve ser curta, clara, respeitosa e conter apenas uma pergunta. "
        "Nao invente fatos que nao estejam no briefing. "
        "Nao responda pelo participante. "
        "Nao use markdown, bullets, explicacoes extras, nem texto fora do JSON."
    )


def build_conversation_prompt(
    session: Session,
    score: int,
    system_questions_asked: int,
    max_questions: int,
    history_text: str,
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
        + f"- Perguntas de aprofundamento ja feitas: {system_questions_asked}\n"
        + f"- Limite maximo de perguntas de aprofundamento: {max_questions}\n"
        + f"- Perguntas restantes possiveis: {questions_remaining}\n"
        + "- Se ja houver contexto suficiente ou o limite tiver sido atingido, responda com should_finish=true.\n"
        + "- Se ainda fizer sentido aprofundar, responda com should_finish=false e gere apenas a proxima pergunta.\n"
        + "- A pergunta deve ter no maximo 220 caracteres.\n"
        + "- A pergunta deve ser aderente ao briefing e ao historico da conversa.\n"
        + "- Evite repeticoes, generalidades vazias e perguntas duplas.\n\n"
        + "Historico da conversa:\n"
        + (history_text or "Sem historico alem da nota inicial.")
    )
