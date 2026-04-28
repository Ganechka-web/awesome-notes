from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import URL
from sqlalchemy.orm import DeclarativeBase

from src.logger import logger


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
        self.async_engine: AsyncEngine = create_async_engine(
            self.postgres_dcn,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_timeout=5,
            echo=False,
        )
        self.session_factory = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Database is connected and ready to execute queries")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager, creates and yields new db session and then closes it"""
        session = self.session_factory()
        try:
            logger.info("Database session created")
            yield session
        finally:
            await session.close()
            logger.info("Database session has closed")
                  
    async def shutdown(self) -> None:
        if self.async_engine:
            await self.async_engine.dispose()
        logger.info("Database has shut down successfully ...")


class Base(DeclarativeBase):
    pass
