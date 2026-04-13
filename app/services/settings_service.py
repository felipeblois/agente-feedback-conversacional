from datetime import datetime
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import get_admin_runtime_meta
from app.models.ai_settings import AISettings
from app.models.settings_audit_log import SettingsAuditLog
from app.schemas.settings import AISettingsUpdate


settings = get_settings()


def _mask_secret(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return f"{value[:4]}...{value[-4:]}"


class SettingsService:
    async def get_or_create(self, db: AsyncSession) -> AISettings:
        result = await db.execute(select(AISettings).limit(1))
        config = result.scalar_one_or_none()
        if config:
            return config

        config = AISettings()
        db.add(config)
        await db.commit()
        await db.refresh(config)
        return config

    async def get_runtime_config(self, db: AsyncSession) -> Dict[str, str]:
        config = await self.get_or_create(db)

        customer_gemini = config.gemini_api_key.strip()
        customer_anthropic = config.anthropic_api_key.strip()
        use_customer = config.credential_mode == "customer"

        if use_customer:
            gemini_key = customer_gemini or settings.gemini_api_key
            anthropic_key = customer_anthropic or settings.anthropic_api_key
            credential_source = "customer"
            if not customer_gemini and not customer_anthropic:
                credential_source = "platform"
        else:
            gemini_key = settings.gemini_api_key
            anthropic_key = settings.anthropic_api_key
            credential_source = "platform"

        return {
            "default_provider": config.default_provider,
            "default_model": config.default_model,
            "fallback_provider": config.fallback_provider,
            "fallback_model": config.fallback_model,
            "gemini_api_key": gemini_key,
            "anthropic_api_key": anthropic_key,
            "credential_source": credential_source,
            "customer_name": config.customer_name,
            "enable_platform_fallback": config.enable_platform_fallback,
        }

    async def get_public_view(self, db: AsyncSession) -> Dict:
        config = await self.get_or_create(db)
        return self._serialize(config)

    async def update(self, db: AsyncSession, payload: AISettingsUpdate, actor: str = "admin") -> Dict:
        config = await self.get_or_create(db)
        data = payload.model_dump()

        gemini_api_key = data.pop("gemini_api_key", None)
        anthropic_api_key = data.pop("anthropic_api_key", None)
        clear_gemini_api_key = data.pop("clear_gemini_api_key", False)
        clear_anthropic_api_key = data.pop("clear_anthropic_api_key", False)
        changed_fields = []

        for field, value in data.items():
            previous = getattr(config, field)
            if previous != value:
                setattr(config, field, value)
                changed_fields.append(field)

        if clear_gemini_api_key:
            config.gemini_api_key = ""
            config.gemini_key_updated_at = datetime.utcnow()
            changed_fields.append("gemini_api_key_cleared")
        elif gemini_api_key is not None:
            config.gemini_api_key = gemini_api_key.strip()
            config.gemini_key_updated_at = datetime.utcnow()
            changed_fields.append("gemini_api_key_updated")
        if clear_anthropic_api_key:
            config.anthropic_api_key = ""
            config.anthropic_key_updated_at = datetime.utcnow()
            changed_fields.append("anthropic_api_key_cleared")
        elif anthropic_api_key is not None:
            config.anthropic_api_key = anthropic_api_key.strip()
            config.anthropic_key_updated_at = datetime.utcnow()
            changed_fields.append("anthropic_api_key_updated")

        db.add(config)
        if changed_fields:
            await self.append_audit_log(
                db,
                area="ai_settings",
                action="update",
                actor=actor,
                details=", ".join(changed_fields),
            )
        await db.commit()
        await db.refresh(config)
        return self._serialize(config)

    async def append_audit_log(
        self,
        db: AsyncSession,
        area: str,
        action: str,
        actor: str,
        details: str,
    ) -> None:
        db.add(
            SettingsAuditLog(
                area=area,
                action=action,
                actor=actor,
                instance_id=settings.instance_id,
                details=details,
            )
        )

    async def list_audit_logs(self, db: AsyncSession, limit: int = 20) -> Dict:
        result = await db.execute(
            select(SettingsAuditLog).order_by(SettingsAuditLog.created_at.desc()).limit(limit)
        )
        items = result.scalars().all()
        return {
            "items": [
                {
                    "id": item.id,
                    "area": item.area,
                    "action": item.action,
                    "actor": item.actor,
                    "instance_id": item.instance_id,
                    "details": item.details,
                    "created_at": item.created_at,
                }
                for item in items
            ]
        }

    def get_security_meta(self) -> Dict:
        return get_admin_runtime_meta()

    def _serialize(self, config: AISettings) -> Dict:
        return {
            "id": config.id,
            "credential_mode": config.credential_mode,
            "customer_name": config.customer_name,
            "default_provider": config.default_provider,
            "default_model": config.default_model,
            "fallback_provider": config.fallback_provider,
            "fallback_model": config.fallback_model,
            "enable_platform_fallback": config.enable_platform_fallback,
            "notes": config.notes,
            "gemini_key_configured": bool(config.gemini_api_key.strip() or settings.gemini_api_key),
            "anthropic_key_configured": bool(config.anthropic_api_key.strip() or settings.anthropic_api_key),
            "gemini_key_masked": _mask_secret(config.gemini_api_key.strip()),
            "anthropic_key_masked": _mask_secret(config.anthropic_api_key.strip()),
            "gemini_key_updated_at": config.gemini_key_updated_at,
            "anthropic_key_updated_at": config.anthropic_key_updated_at,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
        }


settings_service = SettingsService()
