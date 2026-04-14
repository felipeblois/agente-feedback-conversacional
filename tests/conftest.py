from pathlib import Path

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient

from app.core.observability import observability_service
from app.core.database import AsyncSessionLocal
from app.core.security import get_admin_api_token
from app.main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _upgrade_test_database() -> None:
    alembic_cfg = Config(str(PROJECT_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(PROJECT_ROOT / "migrations"))
    command.upgrade(alembic_cfg, "heads")


@pytest.fixture(scope="session", autouse=True)
def ensure_database_schema():
    _upgrade_test_database()
    yield


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
