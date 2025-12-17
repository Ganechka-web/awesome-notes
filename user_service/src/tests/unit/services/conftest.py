import uuid
import random
from datetime import datetime
from typing import TYPE_CHECKING, Generator, Callable

import pytest
from unittest import mock

from src.models.user import User, Gender

if TYPE_CHECKING:
    from src.services.user import UserService


@pytest.fixture
def mock_user_repository(container) -> Generator[mock.AsyncMock, None, None]:
    container.user_repository.override(mock.AsyncMock())
    yield container.user_repository()
    container.user_repository.reset_override()

@pytest.fixture
def mock_user_broker(container) -> Generator[mock.AsyncMock, None, None]:
    container.user_broker.override(mock.AsyncMock())
    yield container.user_broker()
    container.user_broker.reset_override()


@pytest.fixture
def user_service(container) -> "UserService":
    return container.user_service()


@pytest.fixture
def expected_users_orm_with() -> Callable:
    """
    User ORM fabric, allow create one or many with custom attributes if set else random

    Returns:
        User | list[User]
        By default returns single instance but 
        if amount isn`t equal 1, returns list according to amount
    """

    def inner(
        id: uuid.UUID | None = None,
        username: str | None = None,
        gender: str | None = None,
        age: int | None = None,
        amount: int = 1,
    ) -> User | list[User]:
        if amount == 1:
            return User(
                id=id or uuid.uuid4(),
                username=username or "expected_username",
                gender=gender
                or random.choice((Gender.male, Gender.female, Gender.unknown)),
                age=age or random.choice(range(18, 100)),
                joined_at=datetime.now(),
                updated_at=datetime.now(),
            )
        return [
            User(
                id=uuid.uuid4(),
                username=f"{username or 'expected_username'}_{i}",
                gender=gender
                or random.choice((Gender.male, Gender.female, Gender.unknown)),
                age=age or random.choice(range(18, 100)),
                joined_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, amount + 1)
        ]

    return inner
