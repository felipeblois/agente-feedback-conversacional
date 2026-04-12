from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.dependencies import get_db_session
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analysis_service

router = APIRouter()

@router.post("/{session_id}/analyze", response_model=AnalysisResponse)
async def analyze_session(session_id: int, request: AnalysisRequest, db: AsyncSession = Depends(get_db_session)):
    try:
        return await analysis_service.run_analysis(db, session_id, request.provider, request.model)
    except Exception as e:
        logger.error(f"Analysis failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/analysis", response_model=AnalysisResponse)
async def get_latest_analysis(session_id: int, db: AsyncSession = Depends(get_db_session)):
    result = await analysis_service.get_latest(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="No analysis found for this session")
    return result
