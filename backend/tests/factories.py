import random

import factory
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy import select

from backend.models.db_helper import db_helper
from backend.models.tweets import TweetModel
from backend.models.users import UserModel
from backend.services.other_services import get_user_with_following_and_liked_tweets

session = db_helper.get_scoped_session()


class UserFactory(SQLAlchemyModelFactory):
    """Фабрика пользователей."""

    class Meta:
        model = UserModel
        sqlalchemy_session = session

    first_name: str = factory.Faker("first_name")  # type: ignore
    last_name: str = factory.Faker("last_name")  # type: ignore
    email: str = factory.Faker("email")  # type: ignore


class TweetFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Фабрика твитов."""

    class Meta:
        model = TweetModel
        sqlalchemy_session = session

    tweet_data: str = factory.Faker("text")  # type: ignore


async def generate_data() -> None:
    """Генерация данных для тестов."""
    users = UserFactory.create_batch(15)
    await session.commit()

    for user in users:
        TweetFactory.create_batch(10, author=user)
    await session.commit()

    await _generate_subscriptions(users)


async def _generate_subscriptions(users: list[UserModel]) -> None:
    users_db = [
        await get_user_with_following_and_liked_tweets(session, user.id)
        for user in users
    ]

    for user in users_db:
        random_users: list[UserModel] = random.sample(users_db, 6)
        if user in random_users:
            random_users.remove(user)
        user.following = random_users

        await _generate_likes(user, random_users)

    await session.commit()
    await session.close()


async def _generate_likes(user, random_users: list[UserModel]) -> None:
    stmt_select_tweets = select(TweetModel).where(
        TweetModel.author_id.in_([user.id for user in random_users]),
    )
    following_user_tweets = await session.scalars(stmt_select_tweets)

    random_tweets = random.sample(
        following_user_tweets.unique().all(),
        random.randint(1, 5),
    )
    user.liked_tweets = random_tweets
