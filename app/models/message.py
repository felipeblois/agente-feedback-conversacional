import datetime
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    response_id: Mapped[int] = mapped_column(ForeignKey("responses.id", ondelete="CASCADE"))
    sender: Mapped[str] = mapped_column(String(50)) # "system" or "participant"
    message_order: Mapped[int] = mapped_column(Integer)
    message_text: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(50)) # "question", "answer", "score"
    
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    response: Mapped["Response"] = relationship("Response", back_populates="messages")
