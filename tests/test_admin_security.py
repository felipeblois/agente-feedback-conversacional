from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_endpoints_require_authentication(unauthenticated_async_client: AsyncClient):
    dashboard_response = await unauthenticated_async_client.get("/api/v1/sessions/dashboard/summary")
    assert dashboard_response.status_code == 401
    assert dashboard_response.json()["detail"] == "Admin authentication required"

    settings_response = await unauthenticated_async_client.get("/api/v1/settings/ai")
    assert settings_response.status_code == 401

    operational_health = await unauthenticated_async_client.get("/health/operational")
    assert operational_health.status_code == 401


@pytest.mark.asyncio
async def test_public_endpoints_remain_available_without_admin_auth(unauthenticated_async_client: AsyncClient):
    health_response = await unauthenticated_async_client.get("/health")
    assert health_response.status_code == 200

    create_response = await unauthenticated_async_client.post(
        "/api/v1/public/invalid-token/start",
        json={"anonymous": True},
    )
    assert create_response.status_code == 404


@pytest.mark.asyncio
async def test_settings_update_creates_audit_log(async_client: AsyncClient):
    update_response = await async_client.put(
        "/api/v1/settings/ai",
        json={
            "credential_mode": "platform",
            "customer_name": "Cliente teste",
            "default_provider": "gemini",
            "default_model": "gemini-2.5-flash",
            "fallback_provider": "anthropic",
            "fallback_model": "claude-3-5-haiku-20241022",
            "enable_platform_fallback": True,
            "notes": "Ajuste auditado pela suite",
            "clear_gemini_api_key": False,
            "clear_anthropic_api_key": False,
        },
    )
    assert update_response.status_code == 200

    audit_response = await async_client.get("/api/v1/settings/ai/audit")
    assert audit_response.status_code == 200
    payload = audit_response.json()
    assert payload["items"]
    assert any("customer_name" in item["details"] or "notes" in item["details"] for item in payload["items"])


@pytest.mark.asyncio
async def test_admin_meta_exposes_instance_security_context(async_client: AsyncClient):
    response = await async_client.get("/api/v1/settings/admin/meta")
    assert response.status_code == 200
    payload = response.json()
    assert "instance_name" in payload
    assert "instance_id" in payload
    assert "admin_username" in payload
    assert "uses_default_password" in payload


@pytest.mark.asyncio
async def test_bootstrap_admin_login_returns_session_token(unauthenticated_async_client: AsyncClient):
    response = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": "admin", "password": "admin"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["actor"] == "admin"
    assert payload["token"].startswith("session.")


@pytest.mark.asyncio
async def test_nominal_admin_can_be_created_and_login(async_client: AsyncClient, unauthenticated_async_client: AsyncClient):
    username = f"marina_{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/settings/admin/users",
        json={"username": username, "full_name": "Marina Souza", "password": "1234"},
    )
    assert create_response.status_code == 200
    assert create_response.json()["username"] == username

    login_response = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "1234"},
    )
    assert login_response.status_code == 200
    login_payload = login_response.json()
    assert login_payload["actor"] == username
    assert login_payload["source"] == "db_user"

    nominal_client = unauthenticated_async_client
    nominal_client.headers["X-Admin-Token"] = login_payload["token"]

    session_response = await nominal_client.post(
        "/api/v1/sessions",
        json={
            "title": "Sessao da Marina",
            "description": "Criada por admin nominal.",
            "score_type": "workshop",
            "theme_summary": "Autoria",
            "session_goal": "Identificar criador",
            "target_audience": "Gestores",
            "topics_to_explore": "Controle",
            "ai_guidance": "Objetivo",
            "is_anonymous": True,
            "max_followup_questions": 3,
        },
    )
    assert session_response.status_code == 201
    session_payload = session_response.json()
    assert session_payload["created_by_admin_username"] == username
    assert session_payload["updated_by_admin_username"] == username

    await nominal_client.delete(f"/api/v1/sessions/{session_payload['id']}")


@pytest.mark.asyncio
async def test_nominal_admin_can_be_deactivated(async_client: AsyncClient, unauthenticated_async_client: AsyncClient):
    username = f"paula_{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/settings/admin/users",
        json={"username": username, "full_name": "Paula Lima", "password": "1234"},
    )
    assert create_response.status_code == 200
    user_payload = create_response.json()

    update_response = await async_client.patch(
        f"/api/v1/settings/admin/users/{user_payload['id']}",
        json={"full_name": "Paula Lima", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is False

    login_response = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "1234"},
    )
    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_nominal_admin_password_can_be_rotated(async_client: AsyncClient, unauthenticated_async_client: AsyncClient):
    username = f"renata_{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/settings/admin/users",
        json={"username": username, "full_name": "Renata Alves", "password": "1234"},
    )
    assert create_response.status_code == 200
    user_payload = create_response.json()

    rotate_response = await async_client.post(
        f"/api/v1/settings/admin/users/{user_payload['id']}/password",
        json={"password": "4321"},
    )
    assert rotate_response.status_code == 200

    old_login = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "1234"},
    )
    assert old_login.status_code == 401

    new_login = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "4321"},
    )
    assert new_login.status_code == 200
    assert new_login.json()["actor"] == username


@pytest.mark.asyncio
async def test_nominal_admin_can_be_deleted(async_client: AsyncClient, unauthenticated_async_client: AsyncClient):
    username = f"lucia_{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/settings/admin/users",
        json={"username": username, "full_name": "Lucia Prado", "password": "1234"},
    )
    assert create_response.status_code == 200
    user_payload = create_response.json()

    delete_response = await async_client.delete(f"/api/v1/settings/admin/users/{user_payload['id']}")
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    users_response = await async_client.get("/api/v1/settings/admin/users")
    assert users_response.status_code == 200
    usernames = [item["username"] for item in users_response.json()["items"]]
    assert username not in usernames

    login_response = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "1234"},
    )
    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_admin_cannot_delete_own_nominal_user(async_client: AsyncClient, unauthenticated_async_client: AsyncClient):
    username = f"rafa_{uuid4().hex[:8]}"
    create_response = await async_client.post(
        "/api/v1/settings/admin/users",
        json={"username": username, "full_name": "Rafa Costa", "password": "1234"},
    )
    assert create_response.status_code == 200
    user_payload = create_response.json()

    login_response = await unauthenticated_async_client.post(
        "/api/v1/settings/admin/login",
        json={"username": username, "password": "1234"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["token"]

    self_delete_response = await unauthenticated_async_client.delete(
        f"/api/v1/settings/admin/users/{user_payload['id']}",
        headers={"X-Admin-Token": token},
    )
    assert self_delete_response.status_code == 400
    assert self_delete_response.json()["detail"] == "You cannot delete your own admin user"
