from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.api.dependencies import get_db_session
from app.core.config import get_settings
from app.core.observability import log_event
from app.models.session import Session

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
settings = get_settings()

@router.get("/{public_token}")
async def public_chat_page(public_token: str, request: Request, db: AsyncSession = Depends(get_db_session)):
    stmt = select(Session).where(Session.public_token == public_token, Session.status == "active")
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    
    if not session:
        logger.warning(f"Invalid or inactive public_token accessed: {public_token}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or inactive")

    log_event("info", "public_page_rendered", session_id=session.id, public_token=public_token)
        
    return templates.TemplateResponse(
        request,
        "participant_chat.html",
        {
            "session": session,
            "public_token": public_token,
            "retention_policy": {
                "responses_days": settings.retention_responses_days,
                "analyses_days": settings.retention_analyses_days,
                "exports_days": settings.retention_exports_days,
            },
            "privacy_legal_basis_label": settings.privacy_legal_basis_label,
            "privacy_ai_disclaimer": settings.privacy_ai_disclaimer,
            "privacy_contact_email": settings.privacy_contact_email or None,
        },
    )
