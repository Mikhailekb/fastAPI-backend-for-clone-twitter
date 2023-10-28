from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ImageModel
from backend.services.medias_services import (
    add_image_path_to_db,
    delete_image_from_memory,
    get_image,
    get_images_obj_from_ids,
    save_image,
)


async def test_save_image(image_bytes: bytes):
    path = await save_image(image_bytes)
    with open(path, "rb") as f:
        assert f.read()
    Path(path).unlink()


async def test_save_image_not_bytes():
    with pytest.raises(TypeError):
        await save_image("qwerty")


async def test_delete_image_from_memory(image_bytes: bytes):
    path = await save_image(image_bytes)
    with open(path, "rb") as f:
        assert f.read()
    await delete_image_from_memory(path=path)

    with pytest.raises(FileNotFoundError):
        await delete_image_from_memory(path=path)


async def test_get_images_obj_from_ids(db: AsyncSession, image: ImageModel):
    gotten_image = await get_images_obj_from_ids(session=db, image_ids=[image.id])
    assert image.image_path == gotten_image[0].image_path
    await delete_image_from_memory(path=image.image_path)


async def test_add_image_path_to_db(db: AsyncSession, image_bytes: bytes):
    path = await save_image(image_bytes)
    image_id = await add_image_path_to_db(session=db, photo_path=path)
    image = await get_image(session=db, image_id=image_id)

    assert image.image_path == path
    await delete_image_from_memory(path=path)
