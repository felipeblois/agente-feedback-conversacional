"""Demo seed file"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.api.routes.sessions import session_service
from app.schemas.session import SessionCreate

async def seed():
    async with AsyncSessionLocal() as db:
        sess = SessionCreate(
            title="Sessão de Demo Inicial",
            description="Criada automaticamente pelo seed.",
            score_type="nps",
            is_anonymous=True,
            max_followup_questions=3
        )
        print("Criando sessão demo...")
        db_s = await session_service.create(db, sess)
        print(f"Sessão Criada! Link Público: http://localhost:8000/f/{db_s.public_token}")

if __name__ == "__main__":
    asyncio.run(seed())
