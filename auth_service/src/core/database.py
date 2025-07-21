from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import URL

from logger import logger


class AsyncDatabase:
    """AsyncDatabase is a class for managing database connection and session"""

    def __init__(
        self, host: str, port: int, username: str, password: str, db: str
    ) -> None:
        self.postgres_dcn = URL.create(
            drivername="postgresql+asyncpg",
            host=host,
            port=port,
            username=username,
            password=password,
            database=db,
        )
        self.async_engine: AsyncEngine | None = None
        self.session: AsyncSession | None = None

    def _create_async_engine(self) -> None:
        if self.async_engine is None:
            self.async_engine = create_async_engine(self.postgres_dcn, echo=True)
            logger.info("Database is connected and ready to execute queries")

    def get_session(self) -> AsyncSession:
        if self.async_engine is None:
            self._create_async_engine()

        if self.session is None:
            self.session = AsyncSession(bind=self.async_engine)
        return self.session

    async def shutdown(self) -> None:
        if self.session:
            await self.session.aclose()
        logger.info("Database has shut down successfully")


class Base(DeclarativeBase):
    pass
