import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from loguru import logger

from app.models.analysis_run import AnalysisRun
from app.models.response import Response
from app.models.message import Message
from app.services.llm_client import call_llm
from app.services.llm_fallback import llm_fallback
from app.services.theme_service import theme_service

class AnalysisService:
    async def run_analysis(self, db: AsyncSession, session_id: int, provider_param: Optional[str] = None, model_param: Optional[str] = None):
        # Gather all answers
        stmt = select(Message).join(Response).where(Response.session_id == session_id, Message.sender == "participant")
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
        
        all_texts = [m.message_text for m in messages if m.message_text]
        
        # Gather avg score
        stmt_score = select(func.avg(Response.score), func.count()).where(Response.session_id == session_id, Response.score != None)
        score_res = await db.execute(stmt_score)
        row = score_res.fetchone()
        avg_score, count = row if row else (0.0, 0)
        
        provider_used = provider_param or "auto"
        
        if not all_texts:
            return self._create_empty_run(db, session_id, avg_score, count)
            
        full_text = "\n".join(all_texts)
        prompt = f"Analise os seguintes feedbacks de uma sessão de treinamento e gere um resumo em JSON (chaves: summary, positives (lista), negatives (lista), recommendations (lista)). Feedbacks:\n{full_text}"
        
        if provider_param == "fallback":
            llm_response = None
        else:
            llm_response = await call_llm(prompt, "Você é um analista de RH. Retorne APENAS um JSON válido.")
        
        if llm_response:
            try:
                # Naive JSON extract
                start = llm_response.find('{')
                end = llm_response.rfind('}') + 1
                data = json.loads(llm_response[start:end])
                provider_used = provider_param or "llm_auto"
            except Exception as e:
                logger.error(f"Failed to parse JSON from LLM: {e}")
                data = llm_fallback.summarize(all_texts)
                provider_used = "llm_fallback_parse_error"
        else:
            data = llm_fallback.summarize(all_texts)
            provider_used = "static_fallback"
            
        # Create AnalysisRun
        run = AnalysisRun(
            session_id=session_id,
            provider=provider_used,
            model=model_param or "auto",
            summary=data.get("summary", ""),
            positives=data.get("positives", []),
            negatives=data.get("negatives", []),
            recommendations=data.get("recommendations", []),
            avg_score=avg_score,
            response_count=count
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        # For themes we can just run static fallback for now as it's the MVP to speed up
        for msg in messages:
            if msg.message_text:
                themes = llm_fallback.classify_theme(msg.message_text)
                await theme_service.create_themes(db, msg.response_id, themes)

        return await self.get_latest(db, session_id)

    def _create_empty_run(self, db, session_id, avg_score, count):
        return {
            "summary": "Não há texto suficiente para analisar.",
            "top_positive_themes": [],
            "top_negative_themes": [],
            "avg_score": avg_score,
            "response_count": count
        }

    async def get_latest(self, db: AsyncSession, session_id: int):
        stmt = select(AnalysisRun).where(AnalysisRun.session_id == session_id).order_by(AnalysisRun.created_at.desc()).limit(1)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()
        if not run:
            return None
            
        # Naive themes gathering
        from app.models.theme import Theme
        stmt_t = select(Theme.theme_name).join(Response).where(Response.session_id == session_id)
        res_t = await db.execute(stmt_t)
        all_themes = [t for t in res_t.scalars()]
        
        # frequency
        freq = {}
        for t in all_themes:
            freq[t] = freq.get(t, 0) + 1
            
        sorted_themes = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)
        
        return {
            "summary": run.summary,
            "top_positive_themes": sorted_themes[:3], # Simplified for MVP
            "top_negative_themes": sorted_themes[3:6], 
            "avg_score": run.avg_score,
            "response_count": run.response_count
        }

analysis_service = AnalysisService()
