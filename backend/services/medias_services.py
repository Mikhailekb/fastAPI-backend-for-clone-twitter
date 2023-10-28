import io
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import STATIC_DIR
from backend.models import ImageModel


async def get_image(session: AsyncSession, image_id: int) -> ImageModel:
    """
    Получение объекта модели ImageModel по id.

    :raise ValueError: Если объект не найден.
    """
    stmt = select(ImageModel).where(ImageModel.id == image_id)
    if image := await session.scalar(stmt):
        return image
    raise ValueError("Image not found")


async def get_images_obj_from_ids(
    session: AsyncSession,
    image_ids: list[int],
) -> list[ImageModel]:
    """
    Получение списка объектов модели ImageModel из списка id изображений.

    :raise ValueError: Если хотя бы одно изображение не удалось получить.
    """
    stmt = select(ImageModel).where(ImageModel.id.in_(image_ids))
    images_obj = await session.scalars(stmt)
    images = images_obj.all()
    if len(images) != len(image_ids):
        raise ValueError("Image not found")

    return list(images)


async def save_image(image: bytes) -> str:
    """
    Сохранение изображения на диск.
    :raise TypeError: Если полученное изображение не является валидными bytes.
    :return str: Путь к сохраненному изображению.
    """
    try:
        img = Image.open(io.BytesIO(image))
    except UnidentifiedImageError:
        raise TypeError("Not a valid image")

    date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    unique_filename = f"{date}_{uuid4()}.png"
    file_path = STATIC_DIR / "images" / unique_filename
    img.save(
        file_path.absolute(),
        optimize=True,
        quality=80,
        format="PNG",
    )
    return file_path.as_posix()


async def add_image_path_to_db(session: AsyncSession, photo_path: str) -> int:
    """
    Добавление в БД информации о пути файла.
    :return int: id добавленного изображения.
    """
    photo = ImageModel(image_path=photo_path)

    session.add(photo)
    await session.commit()
    return photo.id


async def delete_image_from_memory(path: str) -> None:
    """
    Удаление изображения из памяти.
    :raise FileNotFoundError: Если по полученному пути ничего не найдено.
    """
    Path(path).unlink()
