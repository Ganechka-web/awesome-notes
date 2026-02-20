from typing import Generator
from unittest import mock

import pytest


@pytest.fixture(scope="function")
def mock_auth_service(container) -> Generator[mock.AsyncMock, None, None]:
    container.auth_service.override(mock.AsyncMock())
    yield container.auth_service()
    container.auth_service.reset_override()
