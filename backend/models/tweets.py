from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.base import Base

if TYPE_CHECKING:
    from backend.models.images import ImageModel
    from backend.models.users import UserModel


class TweetModel(Base):
    """Модель твита."""

    __tablename__ = "tweets"

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tweet_data: Mapped[str] = mapped_column(String(500))
    images: Mapped[list["ImageModel"]] = relationship(
        backref="tweet",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    author: Mapped["UserModel"] = relationship(back_populates="tweets", lazy="joined")
    liked_by: Mapped[list["UserModel"]] = relationship(
        secondary="tweets_likes",
        back_populates="liked_tweets",
        lazy="joined",
    )

    @hybrid_property
    def count_likes(self):
        """Подсчитывает количество лайков у данного твита."""
        return len(self.liked_by)
