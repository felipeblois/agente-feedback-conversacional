from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResponseStart(BaseModel):
    participant_name: Optional[str] = None
    participant_email: Optional[str] = None
    anonymous: bool = True

class QuestionDetail(BaseModel):
    type: str # "score" or "text"
    text: str

class StartResponse(BaseModel):
    response_id: int
    first_question: QuestionDetail

class ScoreSubmit(BaseModel):
    response_id: int
    score: int

class ScoreResponse(BaseModel):
    next_question: Optional[QuestionDetail] = None
    conversation_finished: bool = False

class MessageSubmit(BaseModel):
    response_id: int
    message: str

class MessageResponse(BaseModel):
    next_question: Optional[QuestionDetail] = None
    conversation_finished: bool

class FinishResponse(BaseModel):
    response_id: int

class StatusResponse(BaseModel):
    status: str
