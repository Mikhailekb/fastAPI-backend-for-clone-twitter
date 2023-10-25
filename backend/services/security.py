from typing import NoReturn
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.db_helper import db_helper
from backend.models.users import UserModel
from backend.schemas import ExtendedUserSchema

api_key_h = APIKeyHeader(name="api-key")


async def get_user_id_from_api_key(
    request: Request,
    api_key_header: str = Security(api_key_h),
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> int | dict:
    """Проверка API-ключа и получение id юзера."""
    if _is_valid_uuid(api_key_header):
        api_key = api_key_header
    elif api_key_header == "test" and request.get("path") == "/api/users/me":
        return _get_test_user()
    else:
        _raise_forbidden()

    stmt = select(UserModel.id).where(UserModel.api_key == api_key)
    user = await session.scalar(stmt)
    if user:
        return user
    else:
        _raise_forbidden()


def _is_valid_uuid(string) -> bool:
    try:
        UUID(str(string))
    except ValueError:
        return False

    return True


def _raise_forbidden() -> NoReturn:
    raise HTTPException(
        status_code=403,
        detail="Could not validate credentials",
    )


def _get_test_user() -> dict:
    return {
        "result": True,
        "user": ExtendedUserSchema(id=0, name="test").model_dump(),
    }
