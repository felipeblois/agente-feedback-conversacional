import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["Session"] = relationship("Session", back_populates="participants")
    responses: Mapped[List["Response"]] = relationship("Response", back_populates="participant", cascade="all, delete-orphan")
