from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.core.security import require_admin_api_key
from app.core.security import (
    hash_password,
    issue_admin_session_token,
    verify_bootstrap_admin_credentials,
    verify_password,
)
from app.schemas.admin import (
    AdminLoginRequest,
    AdminLoginResponse,
    AdminUserCreateRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdateRequest,
    AdminPasswordUpdateRequest,
)
from app.schemas.settings import (
    SettingsAuditListResponse,
    SettingsSecurityMetaResponse,
    AISettingsResponse,
    AISettingsTestRequest,
    AISettingsTestResponse,
    AISettingsUpdate,
)
from app.services.llm_client import test_provider_connection
from app.services.admin_user_service import admin_user_service
from app.services.settings_service import settings_service


router = APIRouter()


@router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(payload: AdminLoginRequest, db: AsyncSession = Depends(get_db_session)):
    username = (payload.username or "").strip()
    password = payload.password or ""

    if verify_bootstrap_admin_credentials(username, password):
        return {
            "success": True,
            "token": issue_admin_session_token(username, "bootstrap"),
            "actor": username,
            "source": "bootstrap",
        }

    user = await admin_user_service.get_by_username(db, username)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    return {
        "success": True,
        "token": issue_admin_session_token(user.username, "db_user"),
        "actor": user.username,
        "source": "db_user",
    }


@router.get("/ai", response_model=AISettingsResponse)
async def get_ai_settings(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return await settings_service.get_public_view(db)


@router.put("/ai", response_model=AISettingsResponse)
async def update_ai_settings(
    payload: AISettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return await settings_service.update(db, payload, actor="streamlit_admin")


@router.post("/ai/test", response_model=AISettingsTestResponse)
async def test_ai_settings(
    payload: AISettingsTestRequest,
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    try:
        return await test_provider_connection(db, payload.provider, payload.model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/ai/audit", response_model=SettingsAuditListResponse)
async def get_ai_settings_audit(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return await settings_service.list_audit_logs(db)


@router.get("/admin/meta", response_model=SettingsSecurityMetaResponse)
async def get_admin_security_meta(_: str = Depends(require_admin_api_key)):
    return settings_service.get_security_meta()


@router.get("/admin/users", response_model=AdminUserListResponse)
async def list_admin_users(
    db: AsyncSession = Depends(get_db_session),
    _: str = Depends(require_admin_api_key),
):
    return {"items": await admin_user_service.list_users(db)}


@router.post("/admin/users", response_model=AdminUserResponse)
async def create_admin_user(
    payload: AdminUserCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    actor: str = Depends(require_admin_api_key),
):
    username = payload.username.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if len(payload.password or "") < 4:
        raise HTTPException(status_code=400, detail="Password must have at least 4 characters")

    existing = await admin_user_service.get_by_username(db, username)
    if existing:
        raise HTTPException(status_code=409, detail="Admin user already exists")

    user = await admin_user_service.create_user(
        db=db,
        username=username,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        actor=actor,
    )
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_by": user.created_by,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


@router.patch("/admin/users/{user_id}", response_model=AdminUserResponse)
async def update_admin_user(
    user_id: int,
    payload: AdminUserUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    actor: str = Depends(require_admin_api_key),
):
    user = await admin_user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    updated = await admin_user_service.update_user(
        db=db,
        user=user,
        full_name=payload.full_name.strip(),
        is_active=payload.is_active,
    )
    await settings_service.append_audit_log(
        db,
        area="admin_users",
        action="update",
        actor=actor,
        details=f"user={updated.username}, active={updated.is_active}",
    )
    return {
        "id": updated.id,
        "username": updated.username,
        "full_name": updated.full_name,
        "is_active": updated.is_active,
        "created_by": updated.created_by,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.post("/admin/users/{user_id}/password", response_model=AdminUserResponse)
async def update_admin_user_password(
    user_id: int,
    payload: AdminPasswordUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    actor: str = Depends(require_admin_api_key),
):
    if len(payload.password or "") < 4:
        raise HTTPException(status_code=400, detail="Password must have at least 4 characters")
    user = await admin_user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    updated = await admin_user_service.update_password(
        db=db,
        user=user,
        password_hash=hash_password(payload.password),
    )
    await settings_service.append_audit_log(
        db,
        area="admin_users",
        action="password_rotate",
        actor=actor,
        details=f"user={updated.username}",
    )
    return {
        "id": updated.id,
        "username": updated.username,
        "full_name": updated.full_name,
        "is_active": updated.is_active,
        "created_by": updated.created_by,
        "created_at": updated.created_at,
        "updated_at": updated.updated_at,
    }


@router.delete("/admin/users/{user_id}")
async def delete_admin_user(
    user_id: int,
    db: AsyncSession = Depends(get_db_session),
    actor: str = Depends(require_admin_api_key),
):
    user = await admin_user_service.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Admin user not found")
    if user.username == actor:
        raise HTTPException(status_code=400, detail="You cannot delete your own admin user")

    username = user.username
    await admin_user_service.delete_user(db, user)
    await settings_service.append_audit_log(
        db,
        area="admin_users",
        action="delete",
        actor=actor,
        details=f"user={username}",
    )
    return {"success": True, "message": "Admin user deleted successfully"}
