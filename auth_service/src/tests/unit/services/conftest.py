from typing import TYPE_CHECKING, Generator
from unittest import mock

import pytest

if TYPE_CHECKING:
    from src.services.security import SecurityPasswordService
    from src.services.auth import AuthService


@pytest.fixture(scope="session")
def password_service(container) -> "SecurityPasswordService":
    return container.password_service()


@pytest.fixture(scope="module")
def mock_password_service(container) -> Generator[mock.Mock, None, None]:
    origin_provider = container.password_service
    container.password_service.override(mock.Mock())

    yield container.password_service()

    origin_provider.reset_override()


@pytest.fixture(scope="module")
def mock_auth_repository(container) -> Generator[mock.AsyncMock, None, None]:
    origin_provider = container.auth_repository
    container.auth_repository.override(mock.AsyncMock())

    yield container.auth_repository()

    origin_provider.reset_override()


@pytest.fixture(scope="module")
def mock_user_creation_rpc_client(container) -> Generator[mock.AsyncMock, None, None]:
    origin_provider = container.user_creation_rpc_client
    container.user_creation_rpc_client.override(mock.AsyncMock())

    yield container.user_creation_rpc_client()

    origin_provider.reset_override()


@pytest.fixture(scope="class")
def auth_service(container) -> "AuthService":
    return container.auth_service()




