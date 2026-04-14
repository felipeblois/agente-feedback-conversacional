import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.public_access import public_access_service
from app.models.analysis_run import AnalysisRun
from app.models.message import Message
from app.models.participant import Participant
from app.models.response import Response
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate
from app.services.analysis_service import analysis_service
from app.services.export_service import export_service


class SessionService:
    def get_retention_policy(self) -> Dict[str, Any]:
        settings = get_settings()
        return {
            "responses_days": settings.retention_responses_days,
            "analyses_days": settings.retention_analyses_days,
            "logs_days": settings.retention_logs_days,
            "exports_days": settings.retention_exports_days,
            "legal_basis_label": settings.privacy_legal_basis_label,
            "ai_disclaimer": settings.privacy_ai_disclaimer,
            "privacy_contact_email": settings.privacy_contact_email or None,
        }

    async def create(self, db: AsyncSession, obj_in: SessionCreate, actor: Optional[str] = None) -> Session:
        public_token = secrets.token_urlsafe(8)
        db_obj = Session(
            **obj_in.model_dump(),
            public_token=public_token,
            created_by_admin_username=actor,
            updated_by_admin_username=actor,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Session]:
        result = await db.execute(select(Session).where(Session.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(Session)
        if status:
            stmt = stmt.where(Session.status == status)
        stmt = stmt.order_by(Session.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        sessions = list(result.scalars().all())
        return await self._build_session_cards(db, sessions)

    async def get_dashboard_summary(self, db: AsyncSession) -> Dict[str, Any]:
        total_sessions = await db.scalar(select(func.count(Session.id))) or 0
        archived_sessions = await db.scalar(
            select(func.count(Session.id)).where(Session.status == "archived")
        ) or 0
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
            "archived_sessions": archived_sessions,
            "completed_responses": completed_responses,
            "recent_sessions": await self.get_multi(db, skip=0, limit=5, status="active"),
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
        settings = get_settings()
        detail.update(
            {
                "public_url": f"{settings.public_base_url_clean}/f/{session.public_token}",
                "public_link_status": public_access_service.public_link_status(session),
                "score_distribution": score_distribution,
                "recent_responses": recent_responses,
                "latest_analysis_summary": latest_analysis.get("summary") if latest_analysis else None,
            }
        )
        return detail

    async def get_privacy_summary(self, db: AsyncSession, session_id: int) -> Optional[Dict[str, Any]]:
        session = await self.get(db, session_id)
        if not session:
            return None

        participant_rows = await db.execute(
            select(
                func.count(Participant.id).label("total_participants"),
                func.sum(case((Participant.anonymous.is_(False), 1), else_=0)).label(
                    "identified_participants"
                ),
                func.sum(case((Participant.anonymous.is_(True), 1), else_=0)).label(
                    "anonymous_participants"
                ),
            ).where(Participant.session_id == session_id)
        )
        participant_stats = participant_rows.one()

        response_rows = await db.execute(
            select(
                func.count(Response.id).label("total_responses"),
                func.sum(case((Response.status == "completed", 1), else_=0)).label(
                    "completed_responses"
                ),
            ).where(Response.session_id == session_id)
        )
        response_stats = response_rows.one()

        analysis_runs = await db.scalar(
            select(func.count(AnalysisRun.id)).where(AnalysisRun.session_id == session_id)
        ) or 0

        return {
            "session_id": session.id,
            "session_title": session.title,
            "total_participants": participant_stats.total_participants or 0,
            "identified_participants": participant_stats.identified_participants or 0,
            "anonymous_participants": participant_stats.anonymous_participants or 0,
            "total_responses": response_stats.total_responses or 0,
            "completed_responses": response_stats.completed_responses or 0,
            "analysis_runs": analysis_runs,
            "export_files": len(export_service._session_report_files(session_id)),
            "retention_policy": self.get_retention_policy(),
            "session_delete_scope": (
                "Excluir a sessao remove respostas, participantes, analises e exportacoes associadas."
            ),
            "participant_anonymization_scope": (
                "Anonimizar participante remove nome e email, preservando respostas para leitura agregada."
            ),
        }

    async def export_participant_data(
        self,
        db: AsyncSession,
        session_id: int,
        participant_id: int,
    ) -> Optional[Dict[str, Any]]:
        participant = await self._get_session_participant(db, session_id, participant_id)
        if not participant:
            return None

        response_rows = await db.execute(
            select(Response)
            .where(Response.session_id == session_id, Response.participant_id == participant_id)
            .order_by(Response.started_at.asc())
        )
        responses = list(response_rows.scalars().all())

        export_responses: List[Dict[str, Any]] = []
        for response in responses:
            message_rows = await db.execute(
                select(Message)
                .where(Message.response_id == response.id)
                .order_by(Message.message_order.asc(), Message.created_at.asc())
            )
            export_responses.append(
                {
                    "response_id": response.id,
                    "status": response.status,
                    "score": response.score,
                    "started_at": response.started_at,
                    "completed_at": response.completed_at,
                    "messages": [
                        {
                            "message_id": message.id,
                            "sender": message.sender,
                            "message_type": message.message_type,
                            "message_text": message.message_text,
                            "created_at": message.created_at,
                        }
                        for message in message_rows.scalars().all()
                    ],
                }
            )

        return {
            "session_id": session_id,
            "participant_id": participant.id,
            "participant_name": participant.name,
            "participant_email": participant.email,
            "anonymous": participant.anonymous,
            "created_at": participant.created_at,
            "responses": export_responses,
        }

    async def anonymize_participant(
        self,
        db: AsyncSession,
        session_id: int,
        participant_id: int,
    ) -> Optional[Dict[str, Any]]:
        participant = await self._get_session_participant(db, session_id, participant_id)
        if not participant:
            return None

        removed_identifiers = bool(participant.name or participant.email or not participant.anonymous)
        participant.name = None
        participant.email = None
        participant.anonymous = True
        db.add(participant)
        await db.commit()
        await db.refresh(participant)

        response_count = await db.scalar(
            select(func.count(Response.id)).where(
                Response.session_id == session_id,
                Response.participant_id == participant_id,
            )
        ) or 0

        return {
            "session_id": session_id,
            "participant_id": participant.id,
            "anonymous": participant.anonymous,
            "removed_identifiers": removed_identifiers,
            "response_count": response_count,
        }

    async def update(
        self,
        db: AsyncSession,
        db_obj: Session,
        obj_in: SessionUpdate,
        actor: Optional[str] = None,
    ) -> Session:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: int):
        db_obj = await self.get(db, id)
        if db_obj:
            await db.delete(db_obj)
            await db.commit()
            export_service.delete_session_exports(id)

    async def archive(self, db: AsyncSession, id: int, actor: Optional[str] = None) -> Optional[Session]:
        db_obj = await self.get(db, id)
        if not db_obj:
            return None
        db_obj.status = "archived"
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def revoke_public_link(
        self,
        db: AsyncSession,
        id: int,
        actor: Optional[str] = None,
    ) -> Optional[Session]:
        db_obj = await self.get(db, id)
        if not db_obj:
            return None
        db_obj.public_link_enabled = False
        db_obj.public_link_revoked_at = self._utcnow_naive()
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def reactivate_public_link(
        self,
        db: AsyncSession,
        id: int,
        actor: Optional[str] = None,
    ) -> Optional[Session]:
        db_obj = await self.get(db, id)
        if not db_obj:
            return None
        db_obj.public_link_enabled = True
        db_obj.public_link_revoked_at = None
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def rotate_public_token(
        self,
        db: AsyncSession,
        id: int,
        actor: Optional[str] = None,
    ) -> Optional[Session]:
        db_obj = await self.get(db, id)
        if not db_obj:
            return None
        db_obj.public_token = secrets.token_urlsafe(8)
        db_obj.public_link_enabled = True
        db_obj.public_link_revoked_at = None
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def reactivate(self, db: AsyncSession, id: int, actor: Optional[str] = None) -> Optional[Session]:
        db_obj = await self.get(db, id)
        if not db_obj:
            return None
        db_obj.status = "active"
        if actor:
            db_obj.updated_by_admin_username = actor
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

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
                    "theme_summary": session.theme_summary,
                    "session_goal": session.session_goal,
                    "target_audience": session.target_audience,
                    "topics_to_explore": session.topics_to_explore,
                    "ai_guidance": session.ai_guidance,
                    "is_anonymous": session.is_anonymous,
                    "max_followup_questions": session.max_followup_questions,
                    "status": session.status,
                    "created_by_admin_username": session.created_by_admin_username,
                    "updated_by_admin_username": session.updated_by_admin_username,
                    "public_token": session.public_token,
                    "public_link_enabled": session.public_link_enabled,
                    "public_link_expires_at": session.public_link_expires_at,
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

    async def _get_session_participant(
        self,
        db: AsyncSession,
        session_id: int,
        participant_id: int,
    ) -> Optional[Participant]:
        result = await db.execute(
            select(Participant).where(
                Participant.id == participant_id,
                Participant.session_id == session_id,
            )
        )
        return result.scalar_one_or_none()

    def _utcnow_naive(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)


session_service = SessionService()
