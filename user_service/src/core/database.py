import asyncio

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import URL, text
from sqlalchemy.orm import DeclarativeBase

from core.settings import postgres_settings
from logger import logger


postgres_dcn = URL.create(
    drivername="postgresql+asyncpg",
    host=postgres_settings.host,
    port=postgres_settings.port,
    username=postgres_settings.user,
    password=postgres_settings.password,
    database=postgres_settings.db,
).render_as_string(hide_password=False)

async_engine = create_async_engine(postgres_dcn, echo=True)


class Base(DeclarativeBase):
    pass


async def healthcheck() -> None:
    async with async_engine.connect() as conn:
        await conn.execute(text('SELECT 1'))
        await conn.rollback()


async def main():
    try:
        healthcheck_task = asyncio.create_task(healthcheck())
        await asyncio.wait_for(healthcheck_task, timeout=5)

        logger.info('PostgreSQL has connected successfully')
    except (asyncio.TimeoutError, ConnectionRefusedError):
        logger.critical('Connection to PostgreSQL failed')
