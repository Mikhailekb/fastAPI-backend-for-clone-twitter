from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.tweets import TweetModel


class SubscriptionModel(Base):
    """Модель подписки."""

    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "subscribed_to_id",
            name="idx_unique_user_to_user",
        ),
        CheckConstraint(
            "user_id != subscribed_to_id",
            name="ck_user_not_subscribed_to_self",
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subscribed_to_id: Mapped[int] = mapped_column(ForeignKey("users.id"))


class UserModel(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    api_key: Mapped[UUID] = mapped_column(
        default=uuid4,
        server_default=func.gen_random_uuid(),
    )
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(50))

    following: Mapped[list["UserModel"]] = relationship(
        secondary="subscriptions",
        primaryjoin="UserModel.id == SubscriptionModel.user_id",
        secondaryjoin="UserModel.id == SubscriptionModel.subscribed_to_id",
    )

    followers: Mapped[list["UserModel"]] = relationship(
        secondary="subscriptions",
        primaryjoin="UserModel.id == SubscriptionModel.subscribed_to_id",
        secondaryjoin="UserModel.id == SubscriptionModel.user_id",
        viewonly=True,
    )

    liked_tweets: Mapped[list["TweetModel"]] = relationship(
        secondary="tweets_likes",
        back_populates="liked_by",
    )
    tweets: Mapped[list["TweetModel"]] = relationship(back_populates="author")
