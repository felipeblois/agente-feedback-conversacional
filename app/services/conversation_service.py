from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.message import Message
from app.models.response import Response

# Static fallback questions if LLM/Prompts are not fully dynamic
QUESTIONS_MAP = {
    "detractor": [
        "Sinto muito que sua experiência não foi ideal. Qual foi o principal desafio?",
        "O que poderíamos ter feito diferente para melhorar isso para você?",
    ],
    "neutral": [
        "Obrigado pelo feedback! O que faltou para a sessão ser excelente?",
        "Existe algum tópico que você gostaria que tivéssemos aprofundado mais?",
    ],
    "promoter": [
        "Que ótimo saber disso! Qual foi o ponto mais valioso da apresentação?",
        "O que você aprendeu hoje que vai aplicar no seu dia a dia?",
    ]
}

class ConversationService:
    async def get_initial_question(self, score_type: str) -> Dict[str, str]:
        # Typically NPS is 0-10, CSAT 1-5
        text = "De 0 a 10, o quanto você recomendaria esta apresentação para um colega?"
        if score_type == "csat":
            text = "De 1 a 5, quão satisfeito você ficou com o treinamento de hoje?"
        elif score_type == "usefulness":
            text = "De 0 a 10, quão útil foi esta sessão para o seu trabalho?"
            
        return {"type": "score", "text": text}

    async def _get_score_segment(self, score: int, max_val: int = 10) -> str:
        if max_val == 10:
            if score <= 6: return "detractor"
            if score <= 8: return "neutral"
            return "promoter"
        else: # CSAT 1-5 context
            if score <= 3: return "detractor"
            if score == 4: return "neutral"
            return "promoter"

    async def save_user_message(self, db: AsyncSession, response_id: int, text: str):
        # find current max order
        result = await db.execute(select(func.max(Message.message_order)).where(Message.response_id == response_id))
        max_order = result.scalar() or 0
        
        db_obj = Message(
            response_id=response_id,
            sender="participant",
            message_order=max_order + 1,
            message_text=text,
            message_type="answer"
        )
        db.add(db_obj)
        await db.commit()

    async def get_next_question(self, db: AsyncSession, response_id: int, max_questions: int) -> Optional[Dict[str, str]]:
        # Check current count of system questions
        result = await db.execute(select(func.count()).where(Message.response_id == response_id, Message.sender == "system"))
        sys_msg_count = result.scalar() or 0
        
        if sys_msg_count >= max_questions:
            return None # Reached limit
            
        # Get score
        result = await db.execute(select(Response.score).where(Response.id == response_id))
        score = result.scalar()
        if score is None:
            return None
            
        segment = await self._get_score_segment(score)
        
        # In a full AI version, we would prompt the LLM here based on the chat history.
        # For the MVP, we use the fallback map.
        q_list = QUESTIONS_MAP.get(segment, QUESTIONS_MAP["neutral"])
        
        # Pick question based on how many system messages have been sent
        if sys_msg_count < len(q_list):
            q_text = q_list[sys_msg_count]
            
            # Save system question to DB
            order_res = await db.execute(select(func.max(Message.message_order)).where(Message.response_id == response_id))
            max_order = order_res.scalar() or 0
            
            sys_msg = Message(
                response_id=response_id,
                sender="system",
                message_order=max_order + 1,
                message_text=q_text,
                message_type="question"
            )
            db.add(sys_msg)
            await db.commit()
            
            return {"type": "text", "text": q_text}
            
        return None

conversation_service = ConversationService()
