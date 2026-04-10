import secrets
from typing import Any, Dict, List, Optional

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_run import AnalysisRun
from app.models.message import Message
from app.models.participant import Participant
from app.models.response import Response
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate
from app.services.analysis_service import analysis_service


class SessionService:
    async def create(self, db: AsyncSession, obj_in: SessionCreate) -> Session:
        public_token = secrets.token_urlsafe(8)
        db_obj = Session(**obj_in.model_dump(), public_token=public_token)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Session]:
        result = await db.execute(select(Session).where(Session.id == id))
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        stmt = select(Session).order_by(Session.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        sessions = list(result.scalars().all())
        return await self._build_session_cards(db, sessions)

    async def get_dashboard_summary(self, db: AsyncSession) -> Dict[str, Any]:
        total_sessions = await db.scalar(select(func.count(Session.id))) or 0
        total_responses = await db.scalar(select(func.count(Response.id))) or 0
        completed_responses = await db.scalar(
            select(func.count(Response.id)).where(Response.status == "completed")
        ) or 0
        analyses_completed = await db.scalar(select(func.count(AnalysisRun.id))) or 0
        active_sessions = await db.scalar(
            select(func.count(Session.id)).where(Session.status == "active")
        ) or 0
        last_analysis_at = await db.scalar(select(func.max(AnalysisRun.created_at)))
        average_completion_rate = (
            (completed_responses / total_responses) * 100 if total_responses else 0.0
        )

        return {
            "total_sessions": total_sessions,
            "total_responses": total_responses,
            "average_completion_rate": average_completion_rate,
            "analyses_completed": analyses_completed,
            "last_analysis_at": last_analysis_at,
            "active_sessions": active_sessions,
            "completed_responses": completed_responses,
            "recent_sessions": await self.get_multi(db, skip=0, limit=5),
        }

    async def get_detail(self, db: AsyncSession, session_id: int) -> Optional[Dict[str, Any]]:
        session = await self.get(db, session_id)
        if not session:
            return None

        detail = (await self._build_session_cards(db, [session]))[0]

        score_stmt = (
            select(Response.score, func.count(Response.id))
            .where(Response.session_id == session_id, Response.score.is_not(None))
            .group_by(Response.score)
            .order_by(Response.score.asc())
        )
        score_rows = await db.execute(score_stmt)
        score_distribution = [
            {"score": score, "count": count} for score, count in score_rows.all() if score is not None
        ]

        latest_message_subquery = (
            select(Message.message_text)
            .where(Message.response_id == Response.id, Message.sender == "participant")
            .order_by(desc(Message.created_at), desc(Message.message_order))
            .limit(1)
            .scalar_subquery()
        )
        recent_stmt = (
            select(
                Response.id,
                Response.score,
                Response.status,
                Response.started_at,
                Response.completed_at,
                Participant.name,
                Participant.anonymous,
                latest_message_subquery.label("latest_message"),
            )
            .outerjoin(Participant, Participant.id == Response.participant_id)
            .where(Response.session_id == session_id)
            .order_by(desc(Response.started_at))
            .limit(8)
        )
        recent_rows = await db.execute(recent_stmt)
        recent_responses = []
        for row in recent_rows.all():
            recent_responses.append(
                {
                    "response_id": row.id,
                    "participant_label": self._participant_label(row.name, row.anonymous),
                    "score": row.score,
                    "status": row.status,
                    "latest_message": row.latest_message,
                    "started_at": row.started_at,
                    "completed_at": row.completed_at,
                }
            )

        latest_analysis = await analysis_service.get_latest(db, session_id)
        detail.update(
            {
                "public_url": f"http://localhost:8000/f/{session.public_token}",
                "score_distribution": score_distribution,
                "recent_responses": recent_responses,
                "latest_analysis_summary": latest_analysis.get("summary") if latest_analysis else None,
            }
        )
        return detail

    async def update(self, db: AsyncSession, db_obj: Session, obj_in: SessionUpdate) -> Session:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: int):
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()

    async def _build_session_cards(
        self, db: AsyncSession, sessions: List[Session]
    ) -> List[Dict[str, Any]]:
        if not sessions:
            return []

        session_ids = [session.id for session in sessions]
        response_stmt = (
            select(
                Response.session_id,
                func.count(Response.id).label("response_count"),
                func.sum(case((Response.status == "completed", 1), else_=0)).label(
                    "completed_response_count"
                ),
                func.avg(Response.score).label("avg_score"),
            )
            .where(Response.session_id.in_(session_ids))
            .group_by(Response.session_id)
        )
        response_rows = await db.execute(response_stmt)
        response_stats = {
            row.session_id: {
                "response_count": row.response_count or 0,
                "completed_response_count": row.completed_response_count or 0,
                "avg_score": float(row.avg_score) if row.avg_score is not None else None,
            }
            for row in response_rows.all()
        }

        analysis_stmt = (
            select(
                AnalysisRun.session_id,
                func.count(AnalysisRun.id).label("analysis_count"),
                func.max(AnalysisRun.created_at).label("last_analysis_at"),
            )
            .where(AnalysisRun.session_id.in_(session_ids))
            .group_by(AnalysisRun.session_id)
        )
        analysis_rows = await db.execute(analysis_stmt)
        analysis_stats = {
            row.session_id: {
                "analysis_count": row.analysis_count or 0,
                "last_analysis_at": row.last_analysis_at,
            }
            for row in analysis_rows.all()
        }

        cards = []
        for session in sessions:
            response_data = response_stats.get(session.id, {})
            analysis_data = analysis_stats.get(session.id, {})
            response_count = response_data.get("response_count", 0)
            completed_count = response_data.get("completed_response_count", 0)
            completion_rate = (completed_count / response_count * 100) if response_count else 0.0
            cards.append(
                {
                    "id": session.id,
                    "title": session.title,
                    "description": session.description,
                    "score_type": session.score_type,
                    "is_anonymous": session.is_anonymous,
                    "max_followup_questions": session.max_followup_questions,
                    "status": session.status,
                    "public_token": session.public_token,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "response_count": response_count,
                    "completed_response_count": completed_count,
                    "completion_rate": completion_rate,
                    "avg_score": response_data.get("avg_score"),
                    "analysis_count": analysis_data.get("analysis_count", 0),
                    "last_analysis_at": analysis_data.get("last_analysis_at"),
                }
            )
        return cards

    def _participant_label(self, name: Optional[str], anonymous: Optional[bool]) -> str:
        if anonymous:
            return "Anonimo"
        return name or "Participante"


session_service = SessionService()
