from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class TweetLikes(Base):
    """Модель связи пользователя и понравившихся твитов."""

    __tablename__ = "tweets_likes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tweet_id",
            name="idx_unique_user_to_tweet",
        ),
    )

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"))
