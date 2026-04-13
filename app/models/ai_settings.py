import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AISettings(Base):
    __tablename__ = "ai_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    credential_mode: Mapped[str] = mapped_column(String(50), default="platform")
    customer_name: Mapped[str] = mapped_column(String(255), default="")
    gemini_api_key: Mapped[str] = mapped_column(Text, default="")
    anthropic_api_key: Mapped[str] = mapped_column(Text, default="")
    gemini_key_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    anthropic_key_updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)
    default_provider: Mapped[str] = mapped_column(String(50), default="gemini")
    default_model: Mapped[str] = mapped_column(String(100), default="gemini-2.5-flash")
    fallback_provider: Mapped[str] = mapped_column(String(50), default="anthropic")
    fallback_model: Mapped[str] = mapped_column(String(100), default="claude-3-5-haiku-20241022")
    enable_platform_fallback: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
