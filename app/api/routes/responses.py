from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.dependencies import get_db_session
from app.core.observability import log_event
from app.models.session import Session
from app.schemas.response import ResponseStart, StartResponse, ScoreSubmit, ScoreResponse, MessageSubmit, MessageResponse, FinishResponse, StatusResponse
from app.services.response_service import response_service
from app.services.conversation_service import conversation_service

router = APIRouter()

async def get_session_by_token(public_token: str, db: AsyncSession) -> Session:
    stmt = select(Session).where(Session.public_token == public_token, Session.status == "active")
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or inactive")
    return session

@router.post("/{public_token}/start", response_model=StartResponse)
async def start_response(public_token: str, data: ResponseStart, db: AsyncSession = Depends(get_db_session)):
    session = await get_session_by_token(public_token, db)
    
    # Create participant if needed
    participant_name = data.participant_name.strip() if data.participant_name else None
    is_anonymous = data.anonymous or not participant_name
    participant_id = None
    if not is_anonymous:
        participant_id = await response_service.create_participant(
            db,
            session.id,
            participant_name,
            data.participant_email,
        )
    else:
        participant_id = await response_service.create_participant(db, session.id, None, None, anonymous=True)
        
    # Create response entry
    response_id = await response_service.create_response(db, session.id, participant_id)
    
    # Get first question
    first_question = await conversation_service.get_initial_question(session.score_type)
    log_event(
        "info",
        "public_response_started",
        session_id=session.id,
        response_id=response_id,
        participant_mode="anonymous" if is_anonymous else "identified",
    )
    
    return StartResponse(response_id=response_id, first_question=first_question)

@router.post("/{public_token}/score", response_model=ScoreResponse)
async def submit_score(public_token: str, data: ScoreSubmit, db: AsyncSession = Depends(get_db_session)):
    session = await get_session_by_token(public_token, db)
    
    # Save score
    await response_service.update_score(db, data.response_id, data.score)
    log_event(
        "info",
        "public_score_submitted",
        session_id=session.id,
        response_id=data.response_id,
        score=data.score,
    )
    
    # Get next question based on score
    next_step = await conversation_service.get_next_step(db, data.response_id, session.max_followup_questions)
    if next_step["next_question"]:
        return ScoreResponse(
            next_question=next_step["next_question"],
            conversation_finished=False,
            finish_reason=next_step["finish_reason"],
        )

    await response_service.mark_completed(db, data.response_id)
    log_event(
        "info",
        "public_conversation_finished",
        session_id=session.id,
        response_id=data.response_id,
        reason=next_step["finish_reason"],
    )
    return ScoreResponse(
        conversation_finished=True,
        finish_reason=next_step["finish_reason"],
    )

@router.post("/{public_token}/message", response_model=MessageResponse)
async def submit_message(public_token: str, data: MessageSubmit, db: AsyncSession = Depends(get_db_session)):
    session = await get_session_by_token(public_token, db)
    
    # Save user message
    await conversation_service.save_user_message(db, data.response_id, data.message)
    log_event(
        "info",
        "public_message_submitted",
        session_id=session.id,
        response_id=data.response_id,
        message_length=len(data.message or ""),
    )
    
    # Get next question if applicable
    next_step = await conversation_service.get_next_step(db, data.response_id, session.max_followup_questions)
    
    if next_step["next_question"]:
        return MessageResponse(
            next_question=next_step["next_question"],
            conversation_finished=False,
            finish_reason=next_step["finish_reason"],
        )
    else:
        await response_service.mark_completed(db, data.response_id)
        log_event(
            "info",
            "public_conversation_finished",
            session_id=session.id,
            response_id=data.response_id,
            reason=next_step["finish_reason"],
        )
        return MessageResponse(
            conversation_finished=True,
            finish_reason=next_step["finish_reason"],
        )

@router.post("/{public_token}/finish", response_model=StatusResponse)
async def finish_conversation(public_token: str, data: FinishResponse, db: AsyncSession = Depends(get_db_session)):
    session = await get_session_by_token(public_token, db)
    await response_service.mark_completed(db, data.response_id)
    log_event("info", "public_finish_called", session_id=session.id, response_id=data.response_id)
    return StatusResponse(status="completed")
