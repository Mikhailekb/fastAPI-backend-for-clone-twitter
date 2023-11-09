from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from backend.config import MAX_NUMBER
from backend.models.db_helper import db_helper
from backend.schemas import BaseResponse, Error, OutUserSchema
from backend.services.security import get_user_id_from_api_key
from backend.services.users_services import (
    add_follow_user_db,
    delete_follow_user_db,
    serialize_user_extended,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "/{user_id}/follow",
    response_model=BaseResponse,
    responses={404: {"model": Error}, 403: {"model": Error}},
)
async def add_follow_user(
    user_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Create a subscription for a user."""
    if current_user_id == user_id:
        error = Error(error_type="Forbidden", error_message="Can't follow yourself")
        return JSONResponse(status_code=403, content=error.model_dump())

    try:
        await add_follow_user_db(
            session=session,
            user_id=current_user_id,
            follow_user_id=user_id,
        )
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    return BaseResponse()


@router.delete(
    "/{user_id}/follow",
    response_model=BaseResponse,
    responses={404: {"model": Error}},
)
async def delete_follow_user(
    user_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Delete a subscription to a user."""
    try:
        await delete_follow_user_db(
            session=session,
            user_id=current_user_id,
            follow_user_id=user_id,
        )
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    return BaseResponse()


@router.get("/me", response_model=OutUserSchema)
async def get_me_info(
    info: Annotated[int | dict, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
) -> OutUserSchema | dict:
    """Get information about the current user."""
    if isinstance(info, dict):
        return info

    user = await serialize_user_extended(session=session, user_id=info)

    return OutUserSchema(user=user)


@router.get(
    "/{user_id}",
    response_model=OutUserSchema,
    responses={404: {"model": Error}},
)
async def get_user_info(
    user_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    _: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Get information about the specified user."""
    try:
        user = await serialize_user_extended(session=session, user_id=user_id)
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    return OutUserSchema(user=user)
