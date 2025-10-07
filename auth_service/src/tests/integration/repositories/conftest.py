import uuid
from typing import TYPE_CHECKING, AsyncGenerator, Callable, Generator

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from src.models.auth import AuthCredentials
from src.core.settings import postgres_settings
from src.core.database import Base

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase
    from src.repositories.auth import AuthRepository


@pytest.fixture(scope="session", autouse=True)
def postgres_container(container) -> Generator[PostgresContainer, None, None]:
    """
    Starts PostgreSQL test container in docker, sets new host and port in dependencies container.
    Yields working container and stops it.
    """
    postgres_cont = PostgresContainer(
        image="postgres:latest",
        driver="asyncpg",
        username=postgres_settings.user,
        password=postgres_settings.password,
        dbname=postgres_settings.db,
    )
    postgres_cont.start()

    container.config.set(
        "postgres_settings.host", postgres_cont.get_container_host_ip()
    )
    container.config.set("postgres_settings.port", postgres_cont.get_exposed_port(5432))
    container.reset_singletons()

    yield postgres_cont

    postgres_cont.stop()


@pytest_asyncio.fixture(loop_scope="session")
async def prepare_test_database(container) -> AsyncGenerator["AsyncDatabase", None]:
    """
    Creates AsyncDatabase test instance and creates all tables.
    Yields db instance, drops tables and shutdown it.
    """
    test_db = container.auth_database()

    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.commit()

    yield test_db

    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.commit()

    await test_db.shutdown()


@pytest.fixture(scope="function")
def auth_repository(container, prepare_test_database) -> "AuthRepository":
    return container.auth_repository()


@pytest.fixture
def expected_data_with() -> Callable:
    """
    Generate test AuthCredentials instances and their`s attrs according id, login and amount.
    """

    def wrapper(
        id: uuid.UUID | None = None, login: str | None = None, amount: int = 1
    ) -> tuple[list[AuthCredentials], list[dict]]:
        expected_data_orm = []
        expected_data_attrs = []

        if amount == 1:
            attrs = {
                "id": id or uuid.uuid4(),
                "login": login or "some_expectede_login",
                "password": "some_hashed_password",
            }
            expected_data_orm.append(AuthCredentials(**attrs))
            expected_data_attrs.append(attrs)

            return expected_data_orm, expected_data_attrs

        for i in range(1, amount + 1):
            attrs = {
                "id": id or uuid.uuid4(),
                "login": login or f"some_expectede_login_{i}",
                "password": f"some_hashed_password_{i}",
            }
            expected_data_orm.append(AuthCredentials(**attrs))
            expected_data_attrs.append(attrs)

        return expected_data_orm, expected_data_attrs

    return wrapper


@pytest.fixture
def insert_test_data(prepare_test_database) -> Callable:
    """Inserts test data to the test database"""

    async def wrapper(data: list[AuthCredentials]) -> None:
        async with prepare_test_database.get_session() as session:
            session.add_all(data)
            await session.commit()

    return wrapper
