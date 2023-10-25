import pytest
from sqlalchemy import select

from backend.models.db_helper import db_helper
from backend.models.users import UserModel
from backend.tests.factories import UserFactory


@pytest.mark.asyncio
async def test_create_user():
    async with db_helper.session_factory() as session:
        # user = UserFactory()
        user = UserModel(first_name="test", last_name="test", email="test")
        session.add(user)
        await session.commit()
        assert user.id

        stmt = select(UserModel)
        res_user = await session.scalar(stmt)
        assert res_user.id == user.id


# def test_add_follow_user_db(db):
