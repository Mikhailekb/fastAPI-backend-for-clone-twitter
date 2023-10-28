from pathlib import Path
from typing import Final

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    db_host: str = "localhost"
    db_name: str = "dev_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    echo: bool = False
    mode: str = "DEV"

    @property
    def db_url(self) -> str:
        """URL для подключения к базе данных."""
        user_data = f"{self.postgres_user}:{self.postgres_password}"

        return f"postgresql+psycopg://{user_data}@{self.db_host}:5432/{self.db_name}"


settings = Settings()

MAX_NUMBER: Final[int] = 2147483647
BASE_DIR = Path(__name__).parent.parent
STATIC_DIR = BASE_DIR / "static"
