from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.security import get_admin_api_token, verify_admin_session_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_session import AdminSession
from app.models.admin_user import AdminUser


class AdminUserService:
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[AdminUser]:
        result = await db.execute(select(AdminUser).where(AdminUser.username == username))
        return result.scalar_one_or_none()

    async def list_users(self, db: AsyncSession) -> List[Dict]:
        result = await db.execute(select(AdminUser).order_by(AdminUser.created_at.desc()))
        users = result.scalars().all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "created_by": user.created_by,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            }
            for user in users
        ]

    async def create_user(
        self,
        db: AsyncSession,
        username: str,
        full_name: str,
        password_hash: str,
        actor: str,
    ) -> AdminUser:
        user = AdminUser(
            username=username,
            full_name=full_name,
            password_hash=password_hash,
            is_active=True,
            created_by=actor,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def get_by_id(self, db: AsyncSession, user_id: int) -> Optional[AdminUser]:
        result = await db.execute(select(AdminUser).where(AdminUser.id == user_id))
        return result.scalar_one_or_none()

    async def update_user(
        self,
        db: AsyncSession,
        user: AdminUser,
        full_name: str,
        is_active: bool,
    ) -> AdminUser:
        user.full_name = full_name
        user.is_active = is_active
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_password(
        self,
        db: AsyncSession,
        user: AdminUser,
        password_hash: str,
    ) -> AdminUser:
        user.password_hash = password_hash
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, db: AsyncSession, user: AdminUser) -> None:
        await db.delete(user)
        await db.commit()

    async def get_session_payload(self, db: AsyncSession, token: str) -> Dict:
        if token == get_admin_api_token():
            settings = get_settings()
            return {
                "authenticated": True,
                "actor": settings.admin_username,
                "source": "bootstrap_token",
                "expires_at": datetime.utcnow() + timedelta(days=3650),
            }
        payload = verify_admin_session_token(token)
        if not payload:
            raise ValueError("Invalid session token")
        result = await db.execute(select(AdminSession).where(AdminSession.id == payload["session_id"]))
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session not found")
        return {
            "authenticated": True,
            "actor": session.actor_username,
            "source": session.source,
            "expires_at": session.expires_at,
        }


admin_user_service = AdminUserService()
