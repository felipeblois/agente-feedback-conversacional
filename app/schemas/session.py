from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SessionBase(BaseModel):
    title: str
    description: Optional[str] = None
    score_type: str = "nps"
    is_anonymous: bool = True
    max_followup_questions: int = 3
    status: str = "active"

class SessionCreate(SessionBase):
    pass

class SessionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    score_type: Optional[str] = None
    is_anonymous: Optional[bool] = None
    max_followup_questions: Optional[int] = None
    status: Optional[str] = None

class SessionResponse(SessionBase):
    id: int
    public_token: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class SessionListResponse(SessionResponse):
    pass
