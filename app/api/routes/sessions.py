from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.dependencies import get_db_session
from app.core.observability import log_event
from app.core.security import require_admin_api_key
from app.schemas.session import (
    DashboardSummaryResponse,
    SessionCreate,
    SessionDetailResponse,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.services.session_service import session_service

router = APIRouter()

@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.create(db, session_in)
    log_event("info", "session_created", session_id=session.id, title=session.title, score_type=session.score_type)
    return session

@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return await session_service.get_dashboard_summary(db)

@router.get("", response_model=List[SessionListResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    status: str = "active",
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return await session_service.get_multi(db, skip=skip, limit=limit, status=status)

@router.post("/{session_id}/archive", response_model=SessionResponse)
async def archive_session(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.archive(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    log_event("info", "session_archived", session_id=session_id, status=session.status)
    return session

@router.post("/{session_id}/reactivate", response_model=SessionResponse)
async def reactivate_session(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.reactivate(db, id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    log_event("info", "session_reactivated", session_id=session_id, status=session.status)
    return session

@router.get("/{session_id}/detail", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.get_detail(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: int,
    session_in: SessionUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = await session_service.update(db, db_obj=session, obj_in=session_in)
    log_event("info", "session_updated", session_id=session_id, title=updated.title, score_type=updated.score_type)
    return updated

@router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    session = await session_service.get(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await session_service.remove(db, id=session_id)
    log_event("warning", "session_deleted", session_id=session_id)
    return {"status": "deleted"}
