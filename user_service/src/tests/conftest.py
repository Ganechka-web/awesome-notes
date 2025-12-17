from typing import Generator

import pytest
from fastapi.testclient import TestClient
from dependency_injector import containers

from src.main import app
from src.logger import logger


@pytest.fixture(autouse=True)
def disable_logger() -> Generator[None, None, None]:
    logger.disable("src")
    yield
    logger.enable("src")


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="session")
def container(client) -> containers.Container:
    return client.app.container
