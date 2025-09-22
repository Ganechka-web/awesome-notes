from typing import Generator
from unittest import mock

import pytest


@pytest.fixture(scope="function")
def mock_auth_service(container) -> Generator[mock.AsyncMock, None, None]:
    original_provider = container.auth_service
    container.auth_service.override(mock.AsyncMock())

    yield container.auth_service()

    original_provider.reset_override()