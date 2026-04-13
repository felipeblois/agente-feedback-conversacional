from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class ParticipantBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    anonymous: bool = True

class ParticipantCreate(ParticipantBase):
    session_id: int

class ParticipantResponse(ParticipantBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    created_at: datetime
