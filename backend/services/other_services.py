import io
from datetime import datetime
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.images import ImageModel
from backend.models.tweets import TweetModel
from backend.models.users import UserModel


async def get_user(session: AsyncSession, user_id: int) -> UserModel:
    """
    Получение юзера по id.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = select(UserModel).where(UserModel.id == user_id)
    if user := await session.scalar(stmt):
        return user
    raise ValueError("User not found")


async def get_user_with_liked_tweets(
    session: AsyncSession,
    user_id: int,
) -> UserModel:
    """
    Получение юзера по id. Подгружается список понравившихся твитов.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.liked_tweets))
    )
    if user := await session.scalar(stmt):
        return user
    raise ValueError("User not found")


async def get_user_with_following(
    session: AsyncSession,
    user_id: int,
) -> UserModel:
    """
    Получение юзера по id. Подгружается список подписок.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.following))
    )
    if user := await session.scalar(stmt):
        return user
    raise ValueError("User not found")


async def get_user_with_following_and_followers(
    session: AsyncSession,
    user_id: int,
) -> UserModel:
    """
    Получение юзера по id. Подгружается список подписок и подписчиков.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(
            selectinload(UserModel.following),
            selectinload(UserModel.followers),
        )
    )
    if user := await session.scalar(stmt):
        return user
    raise ValueError("User not found")


async def get_user_with_following_and_liked_tweets(
    session: AsyncSession,
    user_id: int,
) -> UserModel:
    """
    Получение юзера по id. Подгружается список подписок и понравившиеся твиты.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(
            selectinload(UserModel.following),
            selectinload(UserModel.liked_tweets),
        )
    )
    if user := await session.scalar(stmt):
        return user
    raise ValueError("User not found")


async def get_tweet(session: AsyncSession, tweet_id: int) -> TweetModel:
    """
    Получение твита по id.

    :raise ValueError: Если твит не найден.
    """
    stmt = select(TweetModel).where(TweetModel.id == tweet_id)
    if tweet := await session.scalar(stmt):
        return tweet
    raise ValueError("Tweet not found")


def get_full_name(user: UserModel) -> str:
    """Получение полного имени юзера."""
    return f"{user.first_name} {user.last_name}"


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


async def save_image(file: UploadFile) -> str:
    """
    Сохранение изображения на диск.
    :return str: Путь к сохраненному изображению.
    """
    image = await file.read()

    img = Image.open(io.BytesIO(image))
    date = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")

    unique_filename = f"{date}_{uuid4()}.png"
    file_path = f"static/images/{unique_filename}"
    img.save(
        file_path,
        optimize=True,
        quality=80,
        format="PNG",
    )
    return file_path


async def add_image_path_to_db(session: AsyncSession, photo_path: str) -> int:
    """
    Добавление в БД информации о пути файла.
    :return int: id добавленного изображения.
    """
    photo = ImageModel(image_path=photo_path)

    session.add(photo)
    await session.commit()
    return photo.id
