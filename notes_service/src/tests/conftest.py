from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.logger import logger
from src.main import app
from src.container import Container


@pytest.fixture(autouse=True)
def disable_logger() -> Generator:
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def container(client) -> Container:
    return client.app.container
