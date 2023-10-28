from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import UserModel
from backend.services.other_services import (
    get_user_with_following,
    get_user_with_following_and_followers,
)
from backend.services.users_services import add_follow_user_db, users_to_schema
from backend.tests.factories import UserFactory, generate_data


async def test_add_follow_user(
    db: AsyncSession,
    client: AsyncClient,
    user: UserModel,
):
    user2 = await UserFactory()
    client.headers = {"api-key": str(user.api_key)}

    response = await client.post(f"/users/{user2.id}/follow")
    assert response.status_code == 200

    user1 = await get_user_with_following(db, user.id)
    user2 = await get_user_with_following_and_followers(db, user2.id)
    assert user1 in user2.followers
    assert user2 in user1.following


async def test_add_follow_user_with_not_exist_user(client: AsyncClient):
    response = await client.post(f"/users/999/follow")
    assert response.status_code == 404


async def test_delete_follow_user(
    db: AsyncSession,
    client: AsyncClient,
    user: UserModel,
) -> None:
    user2 = await UserFactory()
    client.headers = {"api-key": str(user.api_key)}

    await add_follow_user_db(session=db, user_id=user.id, follow_user_id=user2.id)
    response = await client.delete(f"/users/{user2.id}/follow")

    assert response.status_code == 200
    user1 = await get_user_with_following(db, user.id)
    assert user2 not in user1.following


async def test_delete_follow_user_with_not_following_user(client: AsyncClient):
    response = await client.delete(f"/users/999/follow")
    assert response.status_code == 404


async def test_get_me_info(db: AsyncSession, client: AsyncClient) -> None:
    users = await generate_data(db, count_users=3, count_tweets=5)
    user = await get_user_with_following_and_followers(db, users[0].id)

    client.headers = {"api-key": str(user.api_key)}
    response = await client.get("/users/me")
    assert response.status_code == 200

    data = response.json()["user"]
    response_following = await sort_keys(data["following"])
    response_followers = await sort_keys(data["followers"])

    following = await users_to_schema(user.following)
    followers = await users_to_schema(user.followers)
    sample_following = [schema.model_dump() for schema in following]
    sample_followers = [schema.model_dump() for schema in followers]

    assert await sort_keys(sample_following) == response_following
    assert await sort_keys(sample_followers) == response_followers


async def test_get_user_info(
    db: AsyncSession,
    client: AsyncClient,
    user: UserModel,
) -> None:
    users = await generate_data(db, count_users=3, count_tweets=5)
    user2 = await get_user_with_following_and_followers(db, users[1].id)

    client.headers = {"api-key": str(user.api_key)}
    response = await client.get(f"/users/{user2.id}")
    assert response.status_code == 200

    data = response.json()["user"]
    response_following = await sort_keys(data["following"])
    response_followers = await sort_keys(data["followers"])

    following = await users_to_schema(user2.following)
    followers = await users_to_schema(user2.followers)
    sample_following = [schema.model_dump() for schema in following]
    sample_followers = [schema.model_dump() for schema in followers]

    assert await sort_keys(sample_following) == response_following
    assert await sort_keys(sample_followers) == response_followers


async def sort_keys(follow):
    return sorted(follow, key=lambda x: x["id"])


async def test_get_user_info_with_not_exist_user(client: AsyncClient):
    response = await client.get(f"/users/999")
    assert response.status_code == 404
