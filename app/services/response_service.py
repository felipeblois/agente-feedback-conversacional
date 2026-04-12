from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional

from app.models.participant import Participant
from app.models.response import Response

class ResponseService:
    async def create_participant(self, db: AsyncSession, session_id: int, name: Optional[str], email: Optional[str], anonymous: bool = False) -> int:
        db_obj = Participant(
            session_id=session_id,
            name=name,
            email=email,
            anonymous=anonymous
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj.id

    async def create_response(self, db: AsyncSession, session_id: int, participant_id: Optional[int]) -> int:
        db_obj = Response(
            session_id=session_id,
            participant_id=participant_id,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj.id

    async def update_score(self, db: AsyncSession, response_id: int, score: int):
        stmt = update(Response).where(Response.id == response_id).values(score=score)
        await db.execute(stmt)
        await db.commit()

    async def mark_completed(self, db: AsyncSession, response_id: int):
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        stmt = update(Response).where(Response.id == response_id).values(status="completed", completed_at=now)
        await db.execute(stmt)
        await db.commit()

response_service = ResponseService()
