import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import TweetModel, UserModel
from backend.schemas import CreateTweetSchema, TweetSchema, UserSchema
from backend.services.other_services import (
    get_full_name,
    get_tweet,
    get_user_with_following,
    get_user_with_liked_tweets,
)
from backend.services.tweets_services import (
    add_like_to_tweet_db,
    create_tweet_db,
    delete_tweet_db,
    get_tweet_feed_db,
    remove_like_from_tweet_db,
    serialize_tweets,
)
from backend.tests.factories import TweetFactory, generate_data


async def test_create_tweet(db: AsyncSession, user: UserModel):
    tweet = await TweetFactory(author=user)
    assert tweet.id

    stmt = select(TweetModel).where(TweetModel.id == tweet.id)
    res_tweet = await db.scalar(stmt)
    assert res_tweet.id == tweet.id


async def test_get_tweet(db: AsyncSession, tweet: TweetModel):
    res_tweet = await get_tweet(db, tweet.id)
    assert tweet.id == res_tweet.id


async def test_get_non_existent_tweet(db: AsyncSession):
    with pytest.raises(ValueError):
        await get_tweet(db, 999)


async def test_create_tweet_db(db: AsyncSession, user: UserModel):
    tweet_data = "test tweet"
    tweet_id = await create_tweet_db(
        session=db,
        user_id=user.id,
        tweet_data=CreateTweetSchema(tweet_data=tweet_data),
    )

    res_tweet = await get_tweet(db, tweet_id)
    assert res_tweet.tweet_data == tweet_data


async def test_delete_tweet_db(db: AsyncSession, tweet: TweetModel):
    await delete_tweet_db(session=db, tweet_id=tweet.id)

    with pytest.raises(ValueError):
        await get_tweet(db, tweet.id)


async def test_add_like_to_tweet_db(
    db: AsyncSession,
    user: UserModel,
    tweet: TweetModel,
):
    await add_like_to_tweet_db(session=db, user_id=user.id, tweet_id=tweet.id)

    user = await get_user_with_liked_tweets(db, user.id)
    res_tweet = await get_tweet(db, tweet.id)

    assert user in res_tweet.liked_by
    assert res_tweet in user.liked_tweets


async def test_remove_like_from_tweet_db(
    db: AsyncSession,
    user: UserModel,
    tweet: TweetModel,
):
    tweet = await get_tweet(db, tweet.id)

    assert tweet.count_likes == 0
    await add_like_to_tweet_db(session=db, user_id=user.id, tweet_id=tweet.id)

    assert tweet.count_likes == 1
    await remove_like_from_tweet_db(session=db, user_id=user.id, tweet_id=tweet.id)

    assert tweet.count_likes == 0


async def test_get_tweet_feed_db(db: AsyncSession):
    users = await generate_data(db, count_users=3, count_tweets=5)
    user = await get_user_with_following(db, users[0].id)

    tweet_feed = await get_tweet_feed_db(session=db, user_id=user.id)

    for tweet in tweet_feed:
        assert tweet.author in user.following


async def test_serialize_tweets(db: AsyncSession):
    user = UserModel(first_name="first_name", last_name="last_name", email="email")
    tweet1 = TweetModel(tweet_data="test1", author=user)
    tweet2 = TweetModel(tweet_data="test2", author=user)
    db.add(user)
    db.add(tweet1)
    db.add(tweet2)
    await db.commit()

    tweet1 = await get_tweet(db, tweet1.id)
    tweet2 = await get_tweet(db, tweet2.id)

    serialized_tweets = await serialize_tweets([tweet1, tweet2])

    name = get_full_name(user)
    expected_data = [
        TweetSchema(
            id=tweet1.id,
            content=tweet1.tweet_data,
            author=UserSchema(id=user.id, name=name),
        ),
        TweetSchema(
            id=tweet2.id,
            content=tweet2.tweet_data,
            author=UserSchema(id=user.id, name=name),
        ),
    ]

    assert len(serialized_tweets) == 2
    assert serialized_tweets == expected_data
