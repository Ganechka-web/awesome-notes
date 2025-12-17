import uuid
import random
from typing import Generator, Callable
from datetime import datetime
from unittest import mock

import pytest

from src.shemas.user import UserOutputShema
from src.models.user import Gender


@pytest.fixture()
def mock_user_service(container) -> Generator[mock.AsyncMock, None, None]:
    container.user_service.override(mock.AsyncMock())
    yield container.user_service()
    container.user_service.reset_override()


@pytest.fixture
def expected_users_sch_with() -> Callable:
    """
    User schema fabric, allow create one or many with custom attributes if set else random

    Returns:
        UserOutputShema | list[UserOutputShema]
        By default returns single instance but
        if amount isn`t equal 1, returns list according to amount
    """

    def inner(
        id: uuid.UUID | None = None,
        username: str | None = None,
        gender: Gender = Gender.unknown,
        age: int | None = None,
        amount: int = 1,
    ) -> UserOutputShema | list[UserOutputShema]:
        if amount == 1:
            return UserOutputShema(
                id=id or uuid.uuid4(),
                username=username or "some_username",
                gender=gender.value,
                age=age or random.randint(18, 100),
                joined_at=datetime.now(),
                updated_at=datetime.now(),
            )
        return [
            UserOutputShema(
                id=uuid.uuid4(),
                username=username or f"some_username_{i}",
                gender=gender.value,
                age=age or random.randint(18, 100),
                joined_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, amount + 1)
        ]

    return inner
