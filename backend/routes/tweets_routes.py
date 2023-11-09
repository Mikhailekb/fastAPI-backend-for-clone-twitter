from typing import Annotated

from fastapi import APIRouter, Depends, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import MAX_NUMBER
from backend.models.db_helper import db_helper
from backend.schemas import (
    BaseResponse,
    CreateTweetSchema,
    Error,
    OutTweetIDSchema,
    OutTweetsSchema,
)
from backend.services.other_services import get_tweet
from backend.services.security import get_user_id_from_api_key
from backend.services.tweets_services import (
    add_like_to_tweet_db,
    create_tweet_db,
    delete_tweet_db,
    get_tweet_feed_db,
    remove_like_from_tweet_db,
    serialize_tweets,
)

router = APIRouter(prefix="/api/tweets", tags=["tweets"])


@router.post(
    "",
    status_code=201,
    response_model=OutTweetIDSchema,
    responses={400: {"model": Error}},
)
async def add_tweet(
    tweet_data: CreateTweetSchema,
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Create a tweet."""
    try:
        tweet_id = await create_tweet_db(
            session=session,
            user_id=current_user_id,
            tweet_data=tweet_data,
        )
    except ValueError as exc:
        error = Error(error_type="Bad Request", error_message=str(exc))
        return JSONResponse(status_code=400, content=error.model_dump())

    return OutTweetIDSchema(tweet_id=tweet_id)


@router.get("", response_model=OutTweetsSchema)
async def get_tweet_feed(
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Get a tweet feed."""
    model_tweets = await get_tweet_feed_db(session=session, user_id=current_user_id)
    tweets = await serialize_tweets(model_tweets)

    return OutTweetsSchema(tweets=tweets)


@router.delete(
    "/{tweet_id}",
    response_model=BaseResponse,
    responses={403: {"model": Error}, 404: {"model": Error}},
)
async def delete_tweet(
    tweet_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Delete your tweet."""
    try:
        tweet = await get_tweet(session=session, tweet_id=tweet_id)
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    if tweet.author_id != current_user_id:
        error = Error(
            error_type="Forbidden",
            error_message="You are not the author of the tweet",
        )
        return JSONResponse(status_code=403, content=error.model_dump())

    await delete_tweet_db(session=session, tweet_id=tweet_id)
    return BaseResponse()


@router.post(
    "/{tweet_id}/likes",
    response_model=BaseResponse,
    responses={404: {"model": Error}},
)
async def add_like_to_tweet(
    tweet_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Adding a like to a tweet."""
    try:
        await add_like_to_tweet_db(
            session=session,
            user_id=current_user_id,
            tweet_id=tweet_id,
        )
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    return BaseResponse()


@router.delete(
    "/{tweet_id}/likes",
    response_model=BaseResponse,
    responses={404: {"model": Error}},
)
async def remove_like_from_tweet(
    tweet_id: Annotated[int, Path(gt=0, le=MAX_NUMBER)],
    current_user_id: Annotated[int, Depends(get_user_id_from_api_key)],
    session: AsyncSession = Depends(db_helper.scoped_session_dependency),
):
    """Delete your like on a tweet."""
    try:
        await remove_like_from_tweet_db(
            session=session,
            user_id=current_user_id,
            tweet_id=tweet_id,
        )
    except ValueError as exc:
        error = Error(error_type="Not found", error_message=str(exc))
        return JSONResponse(status_code=404, content=error.model_dump())

    return BaseResponse()
