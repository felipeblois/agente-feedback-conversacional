import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.observability import observability_service
from app.core.database import AsyncSessionLocal
from app.core.security import get_admin_api_token
from app.main import app


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-Admin-Token": get_admin_api_token()},
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def unauthenticated_async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def reset_observability():
    observability_service.reset()
    yield
