import json
import re
import time
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.observability import log_event
from app.models.message import Message
from app.models.response import Response
from app.models.session import Session
from app.prompts.conversation_prompt import (
    build_conversation_prompt,
    build_conversation_system_prompt,
)
from app.services.llm_client import call_llm


QUESTIONS_MAP = {
    "detractor": [
        "Qual foi o principal ponto que prejudicou sua experiencia?",
        "Em que momento voce sentiu mais falta de clareza ou direcionamento?",
        "O que deveria ter sido feito de forma diferente para gerar mais valor?",
        "Qual tema merecia mais explicacao ou exemplos mais praticos?",
        "O que faria voce sair desta sessao com uma avaliacao melhor?",
        "Se pudesse ajustar um unico ponto, qual seria?",
    ],
    "neutral": [
        "O que faltou para a sessao ser excelente para voce?",
        "Qual parte teria mais valor com exemplos mais praticos?",
        "Que topico voce gostaria de ver aprofundado em uma proxima edicao?",
        "O que poderia tornar a experiencia mais clara e aplicavel?",
        "Houve algum momento bom, mas que poderia ser ainda melhor?",
        "Que sugestao simples voce daria para evoluir esta sessao?",
    ],
    "promoter": [
        "Qual foi o ponto mais valioso da sessao para voce?",
        "O que voce aprendeu hoje que pretende aplicar no seu dia a dia?",
        "Que elemento tornou esta experiencia especialmente positiva?",
        "Que parte do conteudo ou formato merece ser mantida nas proximas edicoes?",
        "O que mais contribuiu para sua boa avaliacao desta sessao?",
        "Ha algum destaque positivo que valha reforcar para a equipe organizadora?",
    ],
}

FEEDBACK_LABELS = {
    "treinamento": "treinamento",
    "palestra": "palestra",
    "cast": "cast",
    "workshop": "workshop",
    "onboarding": "onboarding",
}

JSON_BLOCK_PATTERN = re.compile(r"\{.*\}", re.DOTALL)
QUESTION_SANITIZE_PATTERN = re.compile(r"\s+")
QUESTION_VALIDATION_PATTERN = re.compile(r"^[^{}<>`]{12,220}\?$")


class ConversationService:
    async def get_initial_question(self, score_type: str) -> Dict[str, str]:
        label = FEEDBACK_LABELS.get(score_type, "sessao")
        text = f"De 0 a 10, como voce avalia este {label}?"
        return {"type": "score", "text": text}

    async def get_next_step(
        self,
        db: AsyncSession,
        response_id: int,
        max_questions: int,
    ) -> Dict[str, object]:
        started_at = time.perf_counter()
        response, session = await self._load_response_context(db, response_id)
        if not response or not session or response.score is None:
            return {"next_question": None, "finished": True, "finish_reason": "missing_context"}

        system_questions_asked = await self._count_system_questions(db, response_id)
        minimum_required = self._minimum_required_questions(max_questions)
        if system_questions_asked >= max_questions:
            log_event(
                "info",
                "conversation_finished",
                session_id=session.id,
                response_id=response_id,
                reason="max_questions_reached",
                questions_asked=system_questions_asked,
                max_questions=max_questions,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {
                "next_question": None,
                "finished": True,
                "finish_reason": "max_questions_reached",
            }

        llm_result = await self._generate_llm_decision(
            db=db,
            response_id=response_id,
            session=session,
            score=response.score,
            system_questions_asked=system_questions_asked,
            max_questions=max_questions,
        )

        if llm_result.get("should_finish") is True and system_questions_asked >= minimum_required:
            log_event(
                "info",
                "conversation_finished",
                session_id=session.id,
                response_id=response_id,
                reason="llm_sufficient_context",
                questions_asked=system_questions_asked,
                minimum_required=minimum_required,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {
                "next_question": None,
                "finished": True,
                "finish_reason": "llm_sufficient_context",
            }

        question_text = llm_result.get("question")
        question_source = llm_result.get("source", "unknown")

        if not question_text:
            question_text = await self._build_fallback_question(
                session=session,
                score=response.score,
                system_questions_asked=system_questions_asked,
                max_questions=max_questions,
            )
            question_source = "fallback"

        if not question_text:
            finish_reason = (
                "fallback_exhausted_after_minimum"
                if system_questions_asked >= minimum_required
                else "no_valid_question_available"
            )
            log_event(
                "info",
                "conversation_finished",
                session_id=session.id,
                response_id=response_id,
                reason=finish_reason,
                questions_asked=system_questions_asked,
                minimum_required=minimum_required,
                duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
            )
            return {"next_question": None, "finished": True, "finish_reason": finish_reason}

        await self._save_system_question(db, response_id, question_text)
        log_event(
            "info",
            "conversation_question_selected",
            session_id=session.id,
            response_id=response_id,
            source=question_source,
            question_index=system_questions_asked + 1,
            max_questions=max_questions,
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return {
            "next_question": {"type": "text", "text": question_text},
            "finished": False,
            "finish_reason": None,
        }

    async def get_next_question(
        self,
        db: AsyncSession,
        response_id: int,
        max_questions: int,
    ) -> Optional[Dict[str, str]]:
        result = await self.get_next_step(db, response_id, max_questions)
        return result.get("next_question")  # backward compatible helper

    async def save_user_message(self, db: AsyncSession, response_id: int, text: str):
        result = await db.execute(
            select(func.max(Message.message_order)).where(Message.response_id == response_id)
        )
        max_order = result.scalar() or 0

        db_obj = Message(
            response_id=response_id,
            sender="participant",
            message_order=max_order + 1,
            message_text=text,
            message_type="answer",
        )
        db.add(db_obj)
        await db.commit()

    async def _load_response_context(
        self,
        db: AsyncSession,
        response_id: int,
    ) -> Tuple[Optional[Response], Optional[Session]]:
        stmt = (
            select(Response, Session)
            .join(Session, Session.id == Response.session_id)
            .where(Response.id == response_id)
        )
        result = await db.execute(stmt)
        row = result.first()
        if not row:
            return None, None
        return row[0], row[1]

    async def _count_system_questions(self, db: AsyncSession, response_id: int) -> int:
        result = await db.execute(
            select(func.count()).where(
                Message.response_id == response_id,
                Message.sender == "system",
            )
        )
        return result.scalar() or 0

    async def _save_system_question(self, db: AsyncSession, response_id: int, q_text: str) -> None:
        order_res = await db.execute(
            select(func.max(Message.message_order)).where(Message.response_id == response_id)
        )
        max_order = order_res.scalar() or 0

        sys_msg = Message(
            response_id=response_id,
            sender="system",
            message_order=max_order + 1,
            message_text=q_text,
            message_type="question",
        )
        db.add(sys_msg)
        await db.commit()

    async def _generate_llm_decision(
        self,
        db: AsyncSession,
        response_id: int,
        session: Session,
        score: int,
        system_questions_asked: int,
        max_questions: int,
    ) -> Dict[str, object]:
        history_text = await self._conversation_history_text(db, response_id)
        prompt = build_conversation_prompt(
            session=session,
            score=score,
            system_questions_asked=system_questions_asked,
            max_questions=max_questions,
            history_text=history_text,
        )

        response = await call_llm(
            db,
            prompt,
            build_conversation_system_prompt(),
            provider_override="gemini",
        )
        if not response:
            log_event(
                "warning",
                "conversation_fallback_engaged",
                session_id=session.id,
                response_id=response_id,
                reason="gemini_unavailable",
            )
            return {"question": None, "should_finish": False, "source": "fallback"}

        parsed = self._parse_llm_payload(response)
        if not parsed:
            log_event(
                "warning",
                "conversation_fallback_engaged",
                session_id=session.id,
                response_id=response_id,
                reason="invalid_llm_payload",
            )
            return {"question": None, "should_finish": False, "source": "fallback"}

        should_finish = bool(parsed.get("should_finish", False))
        question = self._sanitize_question(parsed.get("next_question", ""))

        if should_finish:
            log_event(
                "info",
                "conversation_llm_finish_signal",
                session_id=session.id,
                response_id=response_id,
                question_index=system_questions_asked + 1,
            )
            return {"question": None, "should_finish": True, "source": "gemini"}

        if not self._is_valid_question(question):
            log_event(
                "warning",
                "conversation_fallback_engaged",
                session_id=session.id,
                response_id=response_id,
                reason="invalid_llm_question",
            )
            return {"question": None, "should_finish": False, "source": "fallback"}

        log_event(
            "info",
            "conversation_llm_success",
            session_id=session.id,
            response_id=response_id,
            provider="gemini",
            question_index=system_questions_asked + 1,
        )
        return {"question": question, "should_finish": False, "source": "gemini"}

    async def _conversation_history_text(self, db: AsyncSession, response_id: int) -> str:
        result = await db.execute(
            select(Message.sender, Message.message_text)
            .where(Message.response_id == response_id)
            .order_by(Message.message_order.asc(), Message.created_at.asc())
        )
        parts = []
        for sender, text in result.all():
            role = "IA" if sender == "system" else "Participante"
            parts.append(f"{role}: {text}")
        return "\n".join(parts)

    async def _build_fallback_question(
        self,
        session: Session,
        score: int,
        system_questions_asked: int,
        max_questions: int,
    ) -> Optional[str]:
        segment = await self._get_score_segment(score)
        generated_sequence = self._build_fallback_sequence(session, segment, max_questions)
        if system_questions_asked < len(generated_sequence):
            return generated_sequence[system_questions_asked]
        return None

    def _build_fallback_sequence(
        self,
        session: Session,
        segment: str,
        max_questions: int,
    ) -> List[str]:
        label = FEEDBACK_LABELS.get(session.score_type, "sessao")
        base_questions = list(QUESTIONS_MAP.get(segment, QUESTIONS_MAP["neutral"]))

        briefing_values = [
            ("tema principal", session.theme_summary),
            ("objetivo", session.session_goal),
            ("publico", session.target_audience),
            ("topicos", session.topics_to_explore),
            ("orientacoes", session.ai_guidance),
        ]

        contextual_questions = []
        for field_name, value in briefing_values:
            if not value:
                continue
            snippet = value.strip().rstrip(".")
            if field_name == "tema principal":
                contextual_questions.append(
                    f"Considerando o tema '{snippet}', qual ponto merecia mais destaque neste {label}?"
                )
            elif field_name == "objetivo":
                contextual_questions.append(
                    f"O objetivo '{snippet}' ficou claro e util neste {label}?"
                )
            elif field_name == "publico":
                contextual_questions.append(
                    f"Para o publico '{snippet}', o conteudo deste {label} foi bem direcionado?"
                )
            elif field_name == "topicos":
                contextual_questions.append(
                    f"Entre os topicos '{snippet}', qual deveria ter sido mais aprofundado neste {label}?"
                )
            elif field_name == "orientacoes":
                contextual_questions.append(
                    f"Seguindo a linha '{snippet}', o que mais agregou valor neste {label}?"
                )

        segment_tail = {
            "detractor": [
                f"Qual melhoria mais aumentaria o valor deste {label} para voce?",
                f"Se tivesse prioridade para corrigir um ponto deste {label}, qual seria?",
                f"Qual ajuste pratico faria voce avaliar melhor este {label}?",
                f"Qual parte deste {label} gerou mais frustracao ou atrito?",
            ],
            "neutral": [
                f"Qual ajuste deixaria este {label} mais util para voce?",
                f"Que melhoria simples aumentaria o valor percebido deste {label}?",
                f"Qual ponto voce gostaria de ver mais aprofundado neste {label}?",
                f"O que faltou para este {label} gerar mais impacto para voce?",
            ],
            "promoter": [
                f"Que destaque positivo deste {label} voce acha importante registrar?",
                f"Que aspecto deste {label} mais merece ser mantido nas proximas edicoes?",
                f"Qual ponto forte deste {label} mais contribuiu para sua nota?",
                f"Qual beneficio concreto deste {label} voce leva para a pratica?",
            ],
        }

        final_closer = [
            f"Ha mais algum ponto importante sobre este {label} que voce gostaria de registrar?"
        ]

        sequence = []
        for item in base_questions + contextual_questions + segment_tail.get(segment, []) + final_closer:
            question = self._sanitize_question(item)
            if self._is_valid_question(question) and question not in sequence:
                sequence.append(question)
            if len(sequence) >= max_questions:
                break
        return sequence

    def _minimum_required_questions(self, max_questions: int) -> int:
        return min(max_questions, 2)

    async def _get_score_segment(self, score: int, max_val: int = 10) -> str:
        if max_val == 10:
            if score <= 6:
                return "detractor"
            if score <= 8:
                return "neutral"
            return "promoter"

        if score <= 3:
            return "detractor"
        if score == 4:
            return "neutral"
        return "promoter"

    def _parse_llm_payload(self, raw_text: str) -> Optional[Dict[str, object]]:
        match = JSON_BLOCK_PATTERN.search(raw_text)
        payload = match.group(0) if match else raw_text
        try:
            data = json.loads(payload)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    def _sanitize_question(self, question: str) -> str:
        normalized = QUESTION_SANITIZE_PATTERN.sub(" ", (question or "").strip().strip('"').strip("'"))
        normalized = normalized.replace("??", "?")
        if normalized and "?" not in normalized:
            normalized = f"{normalized.rstrip('.!')}?"
        if normalized.count("?") > 1:
            first_question = normalized.split("?")[0].strip()
            normalized = f"{first_question}?"
        return normalized.strip()

    def _is_valid_question(self, question: str) -> bool:
        if not question:
            return False
        if len(question) > 220:
            return False
        if not QUESTION_VALIDATION_PATTERN.match(question):
            return False
        lowered = question.lower()
        forbidden_snippets = ["json", "```", "{", "}", "responda", "retorne"]
        return not any(snippet in lowered for snippet in forbidden_snippets)


conversation_service = ConversationService()
