from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy import URL
from sqlalchemy.orm import DeclarativeBase

from src.logger import logger


class AsyncDatabase:
    """Asyncdata is a class for managing database connection and session"""

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
        self.async_engine: AsyncEngine = create_async_engine(
            self.postgres_dcn, echo=True
        )
        self.session: AsyncSession | None = None
        logger.info("Database is connected and ready to execute queries")

    def get_session(self) -> AsyncSession:
        if self.session is None:
            self.session = AsyncSession(bind=self.async_engine)
        return self.session

    async def shutdown(self) -> None:
        if self.session:
            await self.session.aclose()
        logger.info("Database has shut down successfully ...")


class Base(DeclarativeBase):
    pass
