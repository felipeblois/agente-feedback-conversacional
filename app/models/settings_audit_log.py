import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SettingsAuditLog(Base):
    __tablename__ = "settings_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    area: Mapped[str] = mapped_column(String(100), default="ai_settings")
    action: Mapped[str] = mapped_column(String(100), default="update")
    actor: Mapped[str] = mapped_column(String(255), default="admin")
    instance_id: Mapped[str] = mapped_column(String(100), default="local-default")
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
