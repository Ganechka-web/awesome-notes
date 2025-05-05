from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import URL
from sqlalchemy.orm import DeclarativeBase

from core.settings import postgres_settings


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
