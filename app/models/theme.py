import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, func
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Theme(Base):
    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"))
    theme_name: Mapped[str] = mapped_column(String(100))
    sentiment: Mapped[Optional[str]] = mapped_column(String(50)) # positive, neutral, negative
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    response: Mapped["Response"] = relationship("Response", back_populates="themes")
