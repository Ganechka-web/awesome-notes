import json
from typing import TYPE_CHECKING, Generator, AsyncGenerator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from testcontainers.postgres import PostgresContainer, DbContainer

from src.main import app
from src.models.auth import AuthCredentials
from src.core.database import Base
from src.logger import logger

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase


@pytest.fixture(autouse=True)
def disable_logging() -> Generator[None, None, None]:
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app=app)


@pytest.fixture(scope="session")
def container(client):
    return client.app.container


@pytest.fixture(scope="session")
def get_postgres_container(container) -> Generator[DbContainer, None, None]:
    postgres_settings = container.config.get("postgres_settings")
    postgres_container = PostgresContainer(
        image="postgres:latest",
        driver="asyncpg",
        username=postgres_settings["user"],
        password=postgres_settings["password"],
        dbname=postgres_settings["db"],
    ).start()

    container.config.set(
        "postgres_settings.host", postgres_container.get_container_host_ip()
    )
    container.config.set(
        "postgres_settings.port", postgres_container.get_exposed_port(5432)
    )
    container.reset_singletons()

    yield postgres_container
    postgres_container.stop()


@pytest_asyncio.fixture(scope="session")
async def get_test_db(get_postgres_container, container) -> AsyncGenerator["AsyncDatabase", None]:
    test_db = container.auth_database()
    yield test_db
    await test_db.shutdown()


@pytest_asyncio.fixture(scope="session")
async def tables(get_test_db: "AsyncDatabase") -> AsyncGenerator[None, None]:
    conn = await get_test_db.async_engine.connect()
    await conn.run_sync(Base.metadata.create_all)
    await conn.commit()
    yield
    await conn.run_sync(Base.metadata.drop_all)
    await conn.aclose()


@pytest_asyncio.fixture(scope="session")
async def insert_test_data(get_test_db: "AsyncDatabase", tables) -> None:
    async with get_test_db.get_session() as session:
        with open("src/tests/repositories/test_db_data.json", "r") as file:
            entities_orm = (AuthCredentials(**entity) for entity in json.load(file))
        session.add_all(entities_orm)
        await session.commit()
