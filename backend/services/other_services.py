from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


async def get_user_with_tweets(
    session: AsyncSession,
    user_id: int,
) -> UserModel:
    """
    Получение юзера по id. Подгружается список твитов.

    :raise ValueError: Если пользователь не найден.
    """
    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id)
        .options(selectinload(UserModel.tweets))
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
