import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Response(Base):
    __tablename__ = "responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    participant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("participants.id", ondelete="SET NULL"))
    score: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), default="started")
    
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    session: Mapped["Session"] = relationship("Session", back_populates="responses")
    participant: Mapped["Participant"] = relationship("Participant", back_populates="responses")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="response", cascade="all, delete-orphan")
    themes: Mapped[List["Theme"]] = relationship("Theme", back_populates="response", cascade="all, delete-orphan")
