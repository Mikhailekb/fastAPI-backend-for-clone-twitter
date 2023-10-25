from asyncio import current_task
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import settings


class DatabaseHelper:
    """Класс для работы с БД."""

    def __init__(self, url: str, echo: bool = False):
        """Инициализируется с параметрами для создания engine."""
        self.engine = create_async_engine(
            url=url,
            echo=echo,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def get_scoped_session(self):
        """Создание и получение объекта асинхронной сессии область действия asyncio."""
        return async_scoped_session(
            session_factory=self.session_factory,
            scopefunc=current_task,
        )

    async def scoped_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        """Возвращает генераторное выражение с асинхронной сессией."""
        session = self.get_scoped_session()
        yield session
        await session.close()


db_helper = DatabaseHelper(
    url=settings.db_url,
    echo=settings.echo,
)
