import asyncio
import io
import sys

import pytest
from httpx import AsyncClient
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.main import app
from backend.models import ImageModel, TweetModel, UserModel
from backend.models.base import Base
from backend.models.db_helper import db_helper
from backend.services.medias_services import add_image_path_to_db, get_image, save_image
from backend.tests.factories import TweetFactory, UserFactory


@pytest.fixture(scope="session")
async def db() -> AsyncSession:
    async for session in db_helper.session_dependency():
        yield session


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


@pytest.fixture
async def client(user: UserModel) -> AsyncClient:
    async with AsyncClient(
        app=app,
        base_url="http://127.0.0.1:5000/api",
        headers={"api-key": str(user.api_key)},
    ) as ac:
        yield ac
        await ac.aclose()


@pytest.fixture
async def user() -> UserModel:
    user: UserModel = await UserFactory()
    return user


@pytest.fixture
async def tweet(user) -> TweetModel:
    tweet = await TweetFactory(author=user)
    return tweet


@pytest.fixture
async def image_bytes() -> bytes:
    image = Image.new("RGB", (100, 100))
    io_obj = io.BytesIO()
    image.save(io_obj, format="JPEG")
    io_obj.seek(0)

    return io_obj.read()


@pytest.fixture
async def image(image_bytes: bytes) -> ImageModel:
    async for session in db_helper.session_dependency():
        path = await save_image(image_bytes)
        image_id = await add_image_path_to_db(session=session, photo_path=path)

        return await get_image(session=session, image_id=image_id)
