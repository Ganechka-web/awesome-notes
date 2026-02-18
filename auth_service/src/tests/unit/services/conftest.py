from typing import TYPE_CHECKING, Generator, Callable, Any
from unittest import mock

import jwt
import pytest

from src.core.settings import ALGORITHM, SECRET_KEY

if TYPE_CHECKING:
    from src.services.security import SecurityPasswordService
    from src.services.auth import AuthService, JWTTokenService


@pytest.fixture(scope="function")
def password_service(container) -> "SecurityPasswordService":
    return container.password_service()


@pytest.fixture(scope="function")
def mock_password_service(container) -> Generator[mock.Mock, None, None]:
    container.password_service.override(mock.Mock())
    yield container.password_service()
    container.password_service.reset_override()


@pytest.fixture(scope="function")
def mock_auth_repository(container) -> Generator[mock.AsyncMock, None, None]:
    container.auth_repository.override(mock.AsyncMock())
    yield container.auth_repository()
    container.auth_repository.reset_override()


@pytest.fixture(scope="function")
def mock_token_service(container) -> Generator[mock.AsyncMock, None, None]:
    with container.token_service.override(mock.AsyncMock()) as token_service_mock:
        yield token_service_mock()


@pytest.fixture(scope="function")
def mock_user_creation_rpc_client(container) -> Generator[mock.AsyncMock, None, None]:
    container.user_creation_rpc_client.override(mock.AsyncMock())
    yield container.user_creation_rpc_client()
    container.user_creation_rpc_client.reset_override()


@pytest.fixture(scope="function")
def auth_service(container) -> "AuthService":
    return container.auth_service()


@pytest.fixture(scope="function")
def mock_redis_token_repository(container) -> Generator[mock.AsyncMock, None, None]:
    with container.redis_token_repository.override(
        mock.AsyncMock()
    ) as redis_token_repository:
        yield redis_token_repository()


@pytest.fixture(scope="function")
def jwt_token_service(container) -> "JWTTokenService":
    return container.token_service()


@pytest.fixture
def decode_jwt_token() -> Callable:
    def inner(token: str) -> dict[str, Any]:
        return jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])

    return inner


@pytest.fixture
def encode_jwt_token() -> Callable:
    def inner(payload: dict[str, Any]) -> str:
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    return inner
