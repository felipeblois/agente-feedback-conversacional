import json
from typing import Optional

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_run import AnalysisRun
from app.models.message import Message
from app.models.response import Response
from app.services.llm_client import call_llm
from app.services.llm_fallback import llm_fallback
from app.services.theme_service import theme_service


class AnalysisService:
    async def run_analysis(
        self,
        db: AsyncSession,
        session_id: int,
        provider_param: Optional[str] = None,
        model_param: Optional[str] = None,
    ):
        stmt = select(Message).join(Response).where(
            Response.session_id == session_id,
            Message.sender == "participant",
        )
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
        all_texts = [m.message_text for m in messages if m.message_text]

        stmt_score = select(func.avg(Response.score), func.count()).where(
            Response.session_id == session_id,
            Response.score.is_not(None),
        )
        score_res = await db.execute(stmt_score)
        row = score_res.fetchone()
        avg_score, count = row if row else (0.0, 0)

        provider_used = provider_param or "auto"
        if not all_texts:
            return self._create_empty_run(avg_score, count)

        full_text = "\n".join(all_texts)
        prompt = (
            "Analise os seguintes feedbacks de uma sessao de treinamento e gere um "
            "resumo em JSON (chaves: summary, positives (lista), negatives (lista), "
            f"recommendations (lista)). Feedbacks:\n{full_text}"
        )

        if provider_param == "fallback":
            llm_response = None
        else:
            llm_response = await call_llm(
                db,
                prompt,
                "Voce e um analista de RH. Retorne APENAS um JSON valido.",
                provider_override=provider_param if provider_param in {"gemini", "anthropic", "openai"} else None,
                model_override=model_param,
            )

        if llm_response:
            try:
                start = llm_response.find("{")
                end = llm_response.rfind("}") + 1
                data = json.loads(llm_response[start:end])
                provider_used = provider_param or "llm_auto"
            except Exception as exc:
                logger.error(f"Failed to parse JSON from LLM: {exc}")
                data = llm_fallback.summarize(all_texts)
                provider_used = "llm_fallback_parse_error"
        else:
            logger.warning(
                f"Analysis fallback engaged | session_id={session_id} | provider=jarvis | reason=cloud_llm_unavailable"
            )
            data = llm_fallback.summarize(all_texts)
            provider_used = "static_fallback"

        run = AnalysisRun(
            session_id=session_id,
            provider=provider_used,
            model=model_param or "auto",
            summary=data.get("summary", ""),
            positives=data.get("positives", []),
            negatives=data.get("negatives", []),
            recommendations=data.get("recommendations", []),
            avg_score=avg_score,
            response_count=count,
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        for msg in messages:
            if msg.message_text:
                themes = llm_fallback.classify_theme(msg.message_text)
                await theme_service.create_themes(db, msg.response_id, themes)

        return await self.get_latest(db, session_id)

    def _create_empty_run(self, avg_score, count):
        return {
            "summary": "Nao ha texto suficiente para analisar.",
            "top_positive_themes": [],
            "top_negative_themes": [],
            "avg_score": avg_score,
            "response_count": count,
            "positives": [],
            "negatives": [],
            "recommendations": [],
            "provider": "empty",
            "model": "n/a",
            "created_at": None,
        }

    async def get_latest(self, db: AsyncSession, session_id: int):
        stmt = (
            select(AnalysisRun)
            .where(AnalysisRun.session_id == session_id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()
        if not run:
            return None

        from app.models.theme import Theme

        stmt_t = select(Theme.theme_name).join(Response).where(Response.session_id == session_id)
        res_t = await db.execute(stmt_t)
        all_themes = [theme for theme in res_t.scalars()]

        freq = {}
        for theme in all_themes:
            freq[theme] = freq.get(theme, 0) + 1
        sorted_themes = sorted(freq.keys(), key=lambda key: freq[key], reverse=True)

        return {
            "summary": run.summary,
            "top_positive_themes": sorted_themes[:3],
            "top_negative_themes": sorted_themes[3:6],
            "avg_score": run.avg_score,
            "response_count": run.response_count,
            "positives": run.positives or [],
            "negatives": run.negatives or [],
            "recommendations": run.recommendations or [],
            "provider": run.provider,
            "model": run.model,
            "created_at": run.created_at,
        }


analysis_service = AnalysisService()
