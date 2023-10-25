import asyncio
import sys
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.config import settings
from backend.main import app
from backend.models.base import Base
from backend.models.db_helper import db_helper
from backend.tests.factories import session as factory_session


@pytest.fixture
def db():
    return db_helper.scoped_session_dependency()


@pytest.fixture(scope="session", autouse=True)
async def prepare_db():
    assert settings.mode == "TEST"

    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
def event_loop(request):
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def ac() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app) as ac:
        yield ac
