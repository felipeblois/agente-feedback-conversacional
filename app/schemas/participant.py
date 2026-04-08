from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ParticipantBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    anonymous: bool = True

class ParticipantCreate(ParticipantBase):
    session_id: int

class ParticipantResponse(ParticipantBase):
    id: int
    session_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
