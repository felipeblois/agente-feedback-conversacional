from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.dependencies import get_db_session
from app.core.observability import log_event
from app.core.security import require_admin_api_key
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analysis_service
from app.services.settings_service import settings_service

router = APIRouter()

@router.post("/{session_id}/analyze", response_model=AnalysisResponse)
async def analyze_session(
    session_id: int,
    request: AnalysisRequest,
    db: AsyncSession = Depends(get_db_session),
    actor: str = Depends(require_admin_api_key),
):
    try:
        result = await analysis_service.run_analysis(db, session_id, request.provider, request.model)
        await settings_service.append_audit_log(
            db,
            area="analysis",
            action="generate",
            actor=actor,
            details=(
                f"session_id={session_id} | provider={result.get('provider')} | "
                f"model={result.get('model')} | responses={result.get('response_count')}"
            ),
        )
        await db.commit()
        log_event(
            "info",
            "analysis_requested",
            session_id=session_id,
            provider=result.get("provider"),
            model=result.get("model"),
            response_count=result.get("response_count"),
        )
        return result
    except Exception as e:
        logger.error(f"Analysis failed for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/analysis", response_model=AnalysisResponse)
async def get_latest_analysis(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    result = await analysis_service.get_latest(db, session_id)
    if not result:
        raise HTTPException(status_code=404, detail="No analysis found for this session")
    log_event("info", "analysis_fetched", session_id=session_id, provider=result.get("provider"), model=result.get("model"))
    return result
