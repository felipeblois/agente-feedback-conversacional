import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AdminSession(Base):
    __tablename__ = "admin_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    actor_username: Mapped[str] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(50), default="session")
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, index=True)
    revoked_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

