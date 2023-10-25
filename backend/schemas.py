from pydantic import BaseModel, Field

from backend.config import MAX_NUMBER


class CreateTweetSchema(BaseModel):
    """Схема для создания твита."""

    tweet_data: str = Field(max_length=500, min_length=1)
    tweet_media_ids: list[int] | None = None


class UserSchema(BaseModel):
    """Базовая схема пользователя."""

    id: int = Field(ge=0, le=MAX_NUMBER)
    name: str


class ExtendedUserSchema(UserSchema):
    """Расширенная схема пользователя."""

    followers: list[UserSchema] = Field(default_factory=list)
    following: list[UserSchema] = Field(default_factory=list)


class TweetLikesSchema(BaseModel):
    """Схема лайка у твита."""

    user_id: int = Field(gt=0, le=MAX_NUMBER)
    name: str


class TweetSchema(BaseModel):
    """Схема твита."""

    id: int = Field(gt=0, le=MAX_NUMBER)
    content: str = Field(max_length=500, min_length=1)
    attachments: list[str] | None = None
    author: UserSchema
    likes: list[TweetLikesSchema] | None = None


class Error(BaseModel):
    """Схема пользовательской ошибки."""

    result: bool = False
    error_type: str
    error_message: str


class BaseResponse(BaseModel):
    """Схема базового успешного ответа."""

    result: bool = True


class OutUserSchema(BaseResponse):
    """Схема ответа с информацией о пользователе."""

    user: ExtendedUserSchema


class OutTweetIDSchema(BaseResponse):
    """Схема ответа с информацией о id твита."""

    tweet_id: int = Field(gt=0, le=MAX_NUMBER)


class OutTweetsSchema(BaseResponse):
    """Схема ответа с твитами."""

    tweets: list[TweetSchema]


class OutMediaSchema(BaseResponse):
    """Схема ответа с id медиа."""

    media_id: int = Field(gt=0, le=MAX_NUMBER)
