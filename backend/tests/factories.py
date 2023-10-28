import random

import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.db_helper import db_helper
from backend.models.tweets import TweetModel
from backend.models.users import UserModel
from backend.services.other_services import (
    get_user_with_following,
    get_user_with_following_and_liked_tweets,
)
from backend.services.tweets_services import get_tweet_feed_db


class UserFactory(SQLAlchemyModelFactory):
    """Фабрика пользователей."""

    class Meta:
        model = UserModel
        sqlalchemy_session = db_helper.session_factory()

    first_name: str = factory.Faker("first_name")  # type: ignore
    last_name: str = factory.Faker("last_name")  # type: ignore
    email: str = factory.Faker("email")  # type: ignore

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        await cls._meta.sqlalchemy_session.commit()
        await cls._meta.sqlalchemy_session.close()

        return instance


class TweetFactory(SQLAlchemyModelFactory):
    """Фабрика твитов."""

    class Meta:
        model = TweetModel
        sqlalchemy_session = db_helper.session_factory()

    tweet_data: str = factory.Faker("text")  # type: ignore

    @classmethod
    async def _create(cls, model_class, *args, **kwargs):
        instance = super()._create(model_class, *args, **kwargs)
        await cls._meta.sqlalchemy_session.commit()
        await cls._meta.sqlalchemy_session.close()

        return instance


async def generate_users(count: int) -> list[UserModel]:
    """Генерация пользователей."""
    return [await UserFactory() for _ in range(count)]  # type: ignore


async def generate_tweets(user: UserModel, count: int) -> list[TweetModel]:
    """Генерация твитов."""
    return [await TweetFactory(author=user) for _ in range(count)]  # type: ignore


async def generate_users_and_tweets(
    count_users: int,
    count_tweets: int,
) -> list[UserModel]:
    """Генерация пользователей и твитов."""
    users = await generate_users(count_users)
    for user in users:
        await generate_tweets(user, count_tweets)

    return users


async def generate_subscriptions(session: AsyncSession, user_ids: list[int]) -> None:
    """Генерация подписок между полученными пользователями."""
    users_db = [
        await get_user_with_following_and_liked_tweets(session, user_id)
        for user_id in user_ids
    ]

    for user in users_db:
        count_following = random.randint(2, len(users_db))
        random_users: list[UserModel] = random.sample(users_db, count_following)

        if user in random_users:
            random_users.remove(user)

        user.following = random_users
    await session.commit()


async def generate_likes(session: AsyncSession, user_id: int) -> None:
    """
    Генерация лайков на посты пользователей из подписок пользователя.
    Ожидается id пользователя, который подписан на других пользователей.
    """
    user = await get_user_with_following(session, user_id)

    following_user_tweets = set()
    for user in user.following:
        tweets = await get_tweet_feed_db(session, user.id)
        following_user_tweets.update(tweets)

    count_liked_tweets = random.randint(1, len(following_user_tweets))

    random_tweets = random.sample(tuple(following_user_tweets), count_liked_tweets)
    user.liked_tweets = random_tweets
    await session.commit()


async def generate_data(
    session: AsyncSession,
    count_users: int = 15,
    count_tweets: int = 5,
) -> list[UserModel]:
    """Генерация данных для тестов."""
    if count_users < 2:
        raise ValueError("Users count should be at least 2")

    users = await generate_users_and_tweets(count_users, count_tweets)
    user_ids = [user.id for user in users]
    await generate_subscriptions(session=session, user_ids=user_ids)
    for user in users:
        await generate_likes(session=session, user_id=user.id)

    return users
