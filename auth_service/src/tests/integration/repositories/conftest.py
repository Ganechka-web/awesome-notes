from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository


@pytest.fixture(scope="session")
def auth_repository(container, insert_test_data) -> "AuthRepository":
    return container.auth_repository()
