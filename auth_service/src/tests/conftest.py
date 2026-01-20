from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.logger import logger
from src.container import Container


@pytest.fixture(scope="session", autouse=True)
def disable_logging() -> Generator[None, None, None]:
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app=app)


@pytest.fixture(scope="session")
def container(client) -> Container:
    """Returns dependencies container"""
    return client.app.container
