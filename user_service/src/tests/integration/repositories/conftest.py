import uuid
import random
from typing import TYPE_CHECKING, Generator, AsyncGenerator, Callable, Any

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer

from src.core.settings import postgres_settings
from src.core.database import AsyncDatabase, Base
from src.models.user import User

if TYPE_CHECKING:
    from src.repositories.user import UserRepository


@pytest.fixture(scope="session", autouse=True)
def postgres_container(container) -> Generator[PostgresContainer, None, None]:
    """
    Creates and starts PostgreSQL container in docker.
    Sets correct variables to dep container.
    Stops container at the end.
    """
    postgres_cont = PostgresContainer(
        image="postgres:latest",
        driver="asyncpg",
        port=postgres_settings.port,
        username=postgres_settings.user,
        password=postgres_settings.password,
        dbname=postgres_settings.db,
    )
    postgres_cont.start()

    container.config.set(
        "postgres_settings.host",
        postgres_cont.get_container_host_ip(),
    )
    container.config.set(
        "postgres_settings.port",
        postgres_cont.get_exposed_port(port=postgres_settings.port),
    )
    container.reset_singletons()

    yield postgres_cont

    postgres_cont.stop()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def prepare_database(container) -> AsyncGenerator[AsyncDatabase, None]:
    """
    Prepares AsyncData to work, creates instance and tables.
    Drops tables and shutdown db at the end
    """
    async_db: AsyncDatabase = container.user_database()

    async with async_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield async_db

    async with async_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await async_db.shutdown()


@pytest.fixture
def user_repository(container) -> "UserRepository":
    return container.user_repository()


@pytest_asyncio.fixture
async def insert_test_data(prepare_database) -> Callable:
    """Inserts list of User ORM to db"""

    async def inner(data: list[User]):
        async with prepare_database.get_session() as session:
            session.add_all(data)
            await session.commit()

    return inner


@pytest.fixture
def expected_users_and_attrs_orm_with() -> Callable:
    """
    User ORM fabric, allow to create one or many with custom attributes.


    Returns:
        by default returns single User instance.
        If amount is greater than 1 return list of Users
        Second returning value is dict contains instances attrs for comparing
    """

    def inner(
        id: uuid.UUID | None = None,
        username: str | None = None,
        gender: str | None = None,
        age: int | None = None,
        amount: int = 1,
    ) -> tuple[User | list[User], dict[str, Any] | list[dict[str, Any]]]:
        if amount == 1:
            user_attrs = {
                "id": id or uuid.uuid4(),
                "username": username or "John_Doe",
                "gender": gender or "unknown",
                "age": age or random.randint(18, 111),
            }
            return User(**user_attrs), user_attrs

        exp_users_attrs = []
        exp_users_orm = []
        for i in range(1, amount + 1):
            attrs = {
                "id": uuid.uuid4(),
                "username": f"John_Doe_{i}",
                "gender": gender or "unknown",
                "age": age or random.randint(18, 111),
            }
            exp_users_attrs.append(attrs)
            exp_users_orm.append(User(**attrs))

        return exp_users_orm, exp_users_attrs

    return inner
