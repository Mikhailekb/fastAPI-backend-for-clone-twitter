from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tweets import TweetModel
from backend.schemas import CreateTweetSchema, TweetLikesSchema, TweetSchema, UserSchema
from backend.services.other_services import (
    get_full_name,
    get_images_obj_from_ids,
    get_tweet,
    get_user_with_following,
    get_user_with_liked_tweets,
)


async def create_tweet_db(
    session: AsyncSession,
    user_id: int,
    tweet_data: CreateTweetSchema,
) -> int:
    """
    Создание твита.

    :raise ValueError: Если изображение используется в другом твите.
    """
    if tweet_data.tweet_media_ids:
        images = await get_images_obj_from_ids(
            session=session,
            image_ids=tweet_data.tweet_media_ids,
        )
        tweet = TweetModel(
            author_id=user_id,
            tweet_data=tweet_data.tweet_data,
            images=images,
        )
        for image in images:
            if image.tweet_id is None:
                image.tweet_id = tweet.id
            else:
                raise ValueError("Image used in more than one tweet")
    else:
        tweet = TweetModel(
            author_id=user_id,
            tweet_data=tweet_data.tweet_data,
        )
    session.add(tweet)
    await session.commit()
    return tweet.id


async def delete_tweet_db(session: AsyncSession, tweet_id: int) -> None:
    """Удаление твита из БД."""
    stmt = delete(TweetModel).where(TweetModel.id == tweet_id)
    await session.execute(stmt)
    await session.commit()


async def add_like_to_tweet_db(
    session: AsyncSession,
    user_id: int,
    tweet_id: int,
) -> None:
    """
    Добавление лайка к твиту.

    :raise ValueError: Если пользователь или твит не найдены.
    """
    user_db = await get_user_with_liked_tweets(session, user_id)
    tweet = await get_tweet(session, tweet_id)

    user_db.liked_tweets.append(tweet)
    await session.commit()


async def delete_like_tweet_db(
    session: AsyncSession,
    user_id: int,
    tweet_id: int,
) -> None:
    """
    Удаление лайка с твита.

    :raise ValueError: Если пользователь или твит не найдены или если
     твита нет в списке понравившихся.
    """
    user_db = await get_user_with_liked_tweets(session, user_id)
    tweet = await get_tweet(session, tweet_id)

    if tweet not in user_db.liked_tweets:
        raise ValueError("Tweet is not in the list of liked tweets")

    user_db.liked_tweets.remove(tweet)
    await session.commit()


async def get_tweet_feed_db(session: AsyncSession, user_id: int) -> list[TweetModel]:
    """
    Получение ленты твитов.

    :raise ValueError: Если пользователь не найден.
    """
    user = await get_user_with_following(session, user_id)
    following_ids = [following_user.id for following_user in user.following]

    stmt = (
        select(TweetModel)
        .where(
            or_(
                TweetModel.author_id.in_(following_ids),
                TweetModel.author_id == user_id,
            ),
        )
        .order_by(TweetModel.count_likes.desc())
    )
    tweets = await session.scalars(stmt)

    return list(tweets.unique().all())


async def serialize_tweets(tweets: list[TweetModel]) -> list[TweetSchema]:
    """Сериализация твитов."""
    out_tweets = []
    for tweet in tweets:
        schema = TweetSchema(
            id=tweet.id,
            content=tweet.tweet_data,
            attachments=[image.image_path for image in tweet.images],
            author=UserSchema(
                id=tweet.author.id,
                name=tweet.author.first_name,
            ),
            likes=[
                TweetLikesSchema(
                    user_id=user.id,
                    name=get_full_name(user),
                )
                for user in tweet.liked_by
            ],
        )

        out_tweets.append(schema)
    return out_tweets
