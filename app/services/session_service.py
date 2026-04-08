import secrets
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.session import Session
from app.schemas.session import SessionCreate, SessionUpdate

class SessionService:
    async def create(self, db: AsyncSession, obj_in: SessionCreate) -> Session:
        public_token = secrets.token_urlsafe(8)
        db_obj = Session(
            **obj_in.model_dump(),
            public_token=public_token
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, id: int) -> Optional[Session]:
        result = await db.execute(select(Session).where(Session.id == id))
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Session]:
        result = await db.execute(select(Session).offset(skip).limit(limit))
        return list(result.scalars().all())

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

session_service = SessionService()
