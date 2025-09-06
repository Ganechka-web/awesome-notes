from typing import TYPE_CHECKING

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src.main import app
from src.tests.db.database import TestDatabase

if TYPE_CHECKING:
    from src.services.security import SecurityPasswordService


@pytest.fixture(scope="session")
def client():
    return TestClient(app=app)


@pytest.fixture(scope="session")
def get_password_service(client: TestClient) -> "SecurityPasswordService":
    return client.app.container.password_service()


@pytest_asyncio.fixture
async def get_test_db():
    db = TestDatabase() 

    await db.create_test_tables()
    yield db
    await db.shutdown()


