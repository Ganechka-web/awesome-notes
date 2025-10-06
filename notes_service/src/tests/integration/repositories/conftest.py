import uuid
import functools
from datetime import datetime
from typing import TYPE_CHECKING, Generator, AsyncGenerator, Callable

import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer, DbContainer

from src.core.settings import postgres_settings
from src.core.database import Base
from src.models.note import Note

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase
    from src.repositories.note import NoteRepository


@pytest.fixture(scope="session", autouse=True)
def postgres_container(container) -> Generator[DbContainer, None, None]:
    postgres_cont = PostgresContainer(
        image="postgres:latest",
        port=postgres_settings.port,
        username=postgres_settings.user,
        password=postgres_settings.password,
        dbname=postgres_settings.db,
    ).start()

    container.config.set(
        "postgres_settings.host", postgres_cont.get_container_host_ip()
    )
    container.config.set(
        "postgres_settings.port", postgres_cont.get_exposed_port(postgres_settings.port)
    )
    container.reset_singletons()

    yield postgres_cont

    postgres_cont.stop()


@pytest_asyncio.fixture(loop_scope="session")
async def prepare_test_database(container) -> AsyncGenerator["AsyncDatabase", None]:
    test_db = container.note_database()

    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_db

    async with test_db.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_db.shutdown()


@pytest.fixture
def note_repository(container, prepare_test_database) -> "NoteRepository":
    return container.note_repository()


@pytest.fixture
def expected_data_with() -> Callable:
    @functools.lru_cache()
    def wrapper(
        id: uuid.UUID | None = None, owner_id: uuid.UUID | None = None, amount: int = 1
    ) -> tuple[list[dict], list[Note]]:
        """
        Returns two lists: 
         - expected_data: bare dicts with Note instances`s attrs 
         - expected_data_on_insert: contains Note ORM instances 
        """
        expected_data = []
        expected_data_on_insert = []
        if amount > 1:
            for i in range(1, amount + 1):
                attrs_data = {
                    "id": id or uuid.uuid4(),
                    "title": f"Some expected title {i}",
                    "content": f"## Some expected md {i}",
                    "owner_id": owner_id or uuid.uuid4(),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
                expected_data.append(attrs_data)
                expected_data_on_insert.append(Note(**attrs_data))
            return (expected_data_on_insert, expected_data)

        attrs_data = {
            "id": id or uuid.uuid4(),
            "title": "Some expected title",
            "content": "## Some expected md",
            "owner_id": owner_id or uuid.uuid4(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }
        expected_data.append(attrs_data)
        expected_data_on_insert.append(Note(**attrs_data))
        return (expected_data_on_insert, expected_data)

    return wrapper


@pytest.fixture
def insert_test_data(prepare_test_database) -> Callable:
    async def wrapper(data: list[Note]) -> None:
        async with prepare_test_database.get_session() as session:
            session.add_all(data)
            await session.commit()

    return wrapper
