import pytest
from sqlalchemy import select
from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.users import UserModel
from backend.services.other_services import (
    get_user,
    get_user_with_following,
    get_user_with_following_and_followers,
)
from backend.services.users_services import add_follow_user_db, delete_follow_user_db
from backend.tests.factories import UserFactory


async def test_create_user(db: AsyncSession):
    user = await UserFactory()
    assert user.id

    stmt = select(UserModel).where(UserModel.id == user.id)
    res_user = await db.scalar(stmt)
    assert res_user.id == user.id


async def test_get_user(db: AsyncSession):
    user = await UserFactory()

    res_user = await get_user(db, user.id)
    assert res_user.id == user.id


async def test_getting_non_existent_user(db: AsyncSession):
    with pytest.raises(ValueError):
        await get_user(db, 999)


async def test_get_user_with_following(user: UserModel, db: AsyncSession) -> None:
    user1 = await get_user(db, user.id)
    user2 = await UserFactory()

    with pytest.raises(MissingGreenlet):
        user1.following.append(user2)

    user_with_following = await get_user_with_following(db, user1.id)
    user2 = await get_user(db, user2.id)
    user_with_following.following.append(user2)

    assert user2 in user_with_following.following


async def test_get_user_with_following_and_followers(db: AsyncSession):
    user1: UserModel = await UserFactory()
    user2 = await UserFactory()
    user3 = await UserFactory()

    user1 = await get_user_with_following_and_followers(db, user1.id)
    user2 = await get_user(db, user2.id)
    user3 = await get_user_with_following(db, user3.id)

    user1.following.append(user2)
    user3.following.append(user1)
    await db.commit()
    await db.refresh(user1)

    assert user2 in user1.following
    assert user3 in user1.followers


async def test_add_follow_user_db(db: AsyncSession):
    user1: UserModel = await UserFactory()
    user2 = await UserFactory()

    await add_follow_user_db(db, user1.id, user2.id)
    user1 = await get_user_with_following(db, user1.id)
    user2 = await get_user(db, user2.id)

    assert user2 in user1.following


async def test_delete_follow_user_db(db: AsyncSession):
    user1: UserModel = await UserFactory()
    user2 = await UserFactory()

    await add_follow_user_db(db, user1.id, user2.id)
    user1 = await get_user_with_following(db, user1.id)
    user2 = await get_user(db, user2.id)

    assert user2 in user1.following
    await delete_follow_user_db(db, user1.id, user2.id)
    assert user2 not in user1.following
