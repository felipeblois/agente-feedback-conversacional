from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict

from app.models.theme import Theme

class ThemeService:
    async def create_themes(self, db: AsyncSession, response_id: int, themes_data: List[Dict]):
        for t_data in themes_data:
            db_obj = Theme(
                response_id=response_id,
                theme_name=t_data.get("theme_name", "Desconhecido"),
                sentiment=t_data.get("sentiment", "neutral"),
                confidence=t_data.get("confidence", 0.0)
            )
            db.add(db_obj)
        await db.commit()

theme_service = ThemeService()
