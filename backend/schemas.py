from pydantic import BaseModel, Field

from backend.config import MAX_NUMBER


class CreateTweetSchema(BaseModel):
    """Schema for creating a tweet."""

    tweet_data: str = Field(max_length=500, min_length=1)
    tweet_media_ids: list[int] = Field(
        default_factory=list,
        description="An array with media file ids. "
        "Media is created via endpoint /api/medias",
    )


class UserSchema(BaseModel):
    """Basic user schema."""

    id: int = Field(ge=0, le=MAX_NUMBER)
    name: str = Field(
        max_length=101,
        description="Full name (first_name + last_name) of the user",
    )


class ExtendedUserSchema(UserSchema):
    """Extended user schema."""

    followers: list[UserSchema] = Field(default_factory=list)
    following: list[UserSchema] = Field(default_factory=list)


class TweetLikesSchema(BaseModel):
    """Tweet like scheme."""

    user_id: int = Field(gt=0, le=MAX_NUMBER)
    name: str = Field(
        max_length=101,
        description="Full name (first_name + last_name) of the user"
        " who liked the tweet",
    )


class TweetSchema(BaseModel):
    """Tweet scheme."""

    id: int = Field(gt=0, le=MAX_NUMBER)
    content: str = Field(max_length=500, min_length=1)
    attachments: list[str] = Field(
        default_factory=list,
        description="Array of paths with media",
    )
    author: UserSchema
    likes: list[TweetLikesSchema] = Field(default_factory=list)


class Error(BaseModel):
    """User error schema."""

    result: bool = False
    error_type: str
    error_message: str


class BaseResponse(BaseModel):
    """Basic successful response schema."""

    result: bool = True


class OutUserSchema(BaseResponse):
    """Response scheme with user information."""

    user: ExtendedUserSchema


class OutTweetIDSchema(BaseResponse):
    """Response scheme with information about tweet id."""

    tweet_id: int = Field(gt=0, le=MAX_NUMBER)


class OutTweetsSchema(BaseResponse):
    """Response scheme with tweets."""

    tweets: list[TweetSchema]


class OutMediaSchema(BaseResponse):
    """Response scheme with media id."""

    media_id: int = Field(gt=0, le=MAX_NUMBER)
