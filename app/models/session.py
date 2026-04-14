import datetime
from sqlalchemy import String, Text, Boolean, Integer, DateTime, func
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text)
    score_type: Mapped[str] = mapped_column(String(50), default="treinamento")
    theme_summary: Mapped[Optional[str]] = mapped_column(Text)
    session_goal: Mapped[Optional[str]] = mapped_column(Text)
    target_audience: Mapped[Optional[str]] = mapped_column(Text)
    topics_to_explore: Mapped[Optional[str]] = mapped_column(Text)
    ai_guidance: Mapped[Optional[str]] = mapped_column(Text)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    max_followup_questions: Mapped[int] = mapped_column(Integer, default=3)
    public_token: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    public_link_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    public_link_expires_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    public_link_revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_by_admin_username: Mapped[Optional[str]] = mapped_column(String(255))
    updated_by_admin_username: Mapped[Optional[str]] = mapped_column(String(255))
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    participants: Mapped[List["Participant"]] = relationship("Participant", back_populates="session", cascade="all, delete-orphan")
    responses: Mapped[List["Response"]] = relationship("Response", back_populates="session", cascade="all, delete-orphan")
    analysis_runs: Mapped[List["AnalysisRun"]] = relationship("AnalysisRun", back_populates="session", cascade="all, delete-orphan")
