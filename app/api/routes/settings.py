from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.schemas.settings import (
    AISettingsResponse,
    AISettingsTestRequest,
    AISettingsTestResponse,
    AISettingsUpdate,
)
from app.services.llm_client import test_provider_connection
from app.services.settings_service import settings_service


router = APIRouter()


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings(db: AsyncSession = Depends(get_db_session)):
    return await settings_service.get_public_view(db)


@router.put("/ai", response_model=AISettingsResponse)
async def update_ai_settings(payload: AISettingsUpdate, db: AsyncSession = Depends(get_db_session)):
    return await settings_service.update(db, payload)


@router.post("/ai/test", response_model=AISettingsTestResponse)
async def test_ai_settings(payload: AISettingsTestRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        return await test_provider_connection(db, payload.provider, payload.model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
