import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ImageModel, TweetModel
from backend.services.medias_services import delete_image_from_memory, get_image
from backend.services.other_services import (
    get_tweet,
    get_user,
    get_user_with_liked_tweets,
    get_user_with_tweets,
)
from backend.services.tweets_services import add_like_to_tweet_db
from backend.tests.factories import generate_data


async def test_add_tweet(db: AsyncSession, client: AsyncClient):
    response = await client.post("/tweets", json={"tweet_data": "test"})
    assert response.status_code == 201

    tweet = response.json()
    tweet_id = tweet["tweet_id"]
    stmt = select(TweetModel).where(TweetModel.id == tweet_id)

    tweet_db: TweetModel = await db.scalar(stmt)

    assert tweet_db.id == tweet_id


async def test_add_tweet_with_invalid_tweet_media_ids(client: AsyncClient):
    data = {"tweet_data": "test", "tweet_media_ids": [999]}
    response = await client.post("/tweets", json=data)
    assert response.status_code == 400


async def test_add_tweet_with_invalid_tweet_data(client: AsyncClient):
    response = await client.post("/tweets", json={"tweet_data": ""})
    assert response.status_code == 422


async def test_upload_medias(db: AsyncSession, client: AsyncClient, image_bytes: bytes):
    response = await client.post(
        "/medias", files={"file": ("image.jpg", image_bytes, "image/jpeg")}
    )
    assert response.status_code == 201

    image_id = response.json()["media_id"]
    image = await get_image(session=db, image_id=image_id)
    assert image

    await delete_image_from_memory(path=image.image_path)


async def test_upload_medias_with_no_image(client: AsyncClient):
    response = await client.post(
        "/medias", files={"file": ("image.jpg", "no_bytes", "image/jpeg")}
    )
    assert response.status_code == 415


async def test_add_tweet_with_image(
    db: AsyncSession,
    image: ImageModel,
    client: AsyncClient,
):
    assert image.tweet_id is None

    data = {"tweet_data": "test", "tweet_media_ids": [image.id]}
    response = await client.post("/tweets", json=data)
    assert response.status_code == 201

    tweet = response.json()
    tweet_id = tweet["tweet_id"]
    tweet_db = await get_tweet(db, tweet_id)

    assert tweet_db.id == tweet_id
    image = await get_image(session=db, image_id=image.id)

    assert image.tweet_id == tweet_db.id
    assert tweet_db.images == [image]

    await delete_image_from_memory(path=image.image_path)


async def test_get_tweet_feed(db: AsyncSession, client: AsyncClient):
    users = await generate_data(db, count_users=3, count_tweets=5)
    user = await get_user(db, users[0].id)
    client.headers = {"api-key": str(user.api_key)}

    response = await client.get("/tweets")
    assert response.status_code == 200
    assert len(response.json()["tweets"]) > 1


async def test_delete_tweet(db: AsyncSession, client: AsyncClient):
    users = await generate_data(db, count_users=3, count_tweets=5)
    user = await get_user_with_tweets(db, users[0].id)
    client.headers = {"api-key": str(user.api_key)}
    tweet = user.tweets[0]

    response = await client.delete(f"/tweets/{tweet.id}")
    assert response.status_code == 200

    with pytest.raises(ValueError):
        await get_tweet(db, tweet.id)


async def test_add_like_to_tweet(db: AsyncSession, client: AsyncClient):
    users = await generate_data(db, count_users=3, count_tweets=5)
    user1 = await get_user_with_liked_tweets(db, users[0].id)
    user2 = await get_user_with_tweets(db, users[1].id)

    client.headers = {"api-key": str(user1.api_key)}
    tweet = user2.tweets[0]

    if tweet in user1.liked_tweets:
        user1.liked_tweets.remove(tweet)

    response = await client.post(f"/tweets/{tweet.id}/likes")
    assert response.status_code == 200
    await db.refresh(user1)
    assert tweet in user1.liked_tweets


async def test_remove_like_from_tweet(db: AsyncSession, client: AsyncClient):
    users = await generate_data(db, count_users=3, count_tweets=5)
    user1 = await get_user_with_liked_tweets(db, users[0].id)
    user2 = await get_user_with_tweets(db, users[1].id)

    client.headers = {"api-key": str(user1.api_key)}
    tweet = user2.tweets[0]

    await add_like_to_tweet_db(session=db, user_id=user1.id, tweet_id=tweet.id)
    await db.refresh(user1)
    assert tweet in user1.liked_tweets

    response = await client.delete(f"/tweets/{tweet.id}/likes")
    assert response.status_code == 200
    await db.refresh(user1)
    assert tweet not in user1.liked_tweets
