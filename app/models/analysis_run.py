import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func, JSON
from typing import Optional, Union
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(50))
    model: Mapped[str] = mapped_column(String(100))
    summary: Mapped[str] = mapped_column(Text)
    positives: Mapped[Optional[Union[dict, list]]] = mapped_column(JSON)
    negatives: Mapped[Optional[Union[dict, list]]] = mapped_column(JSON)
    recommendations: Mapped[Optional[Union[dict, list]]] = mapped_column(JSON)
    avg_score: Mapped[Optional[float]] = mapped_column(Float)
    response_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["Session"] = relationship("Session", back_populates="analysis_runs")
