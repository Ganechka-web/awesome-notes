import json
from typing import TYPE_CHECKING

import pytest_asyncio
from sqlalchemy import text

from src.models.auth import AuthCredentials
from src.repositories.auth import AuthRepository

if TYPE_CHECKING:
    from tests.db.database import TestDatabase


@pytest_asyncio.fixture
async def insert_test_data(get_test_db: "TestDatabase"):
    async with get_test_db.async_database.get_session() as session:
        # gets test data from file
        with open(r"src/tests/repositories/test_db_data.json", "r", encoding="utf-8") as file:
            entities = [AuthCredentials(**entity) for entity in json.load(file)]
        session.add_all(entities)
        await session.commit()
        yield
        # delete all rows
        await session.execute(text("TRUNCATE TABLE auth_credentials"))


@pytest_asyncio.fixture
async def get_auth_repository(get_test_db: "TestDatabase"):
    return AuthRepository(database=get_test_db.async_database)
