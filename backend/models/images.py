from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.models.base import Base


class ImageModel(Base):
    """Модель изображения."""

    __tablename__ = "images"

    image_path: Mapped[str] = mapped_column(String(128))
    tweet_id: Mapped[int | None] = mapped_column(
        ForeignKey("tweets.id", ondelete="CASCADE"),
    )
