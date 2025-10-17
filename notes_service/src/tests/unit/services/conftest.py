import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Generator, Callable
from unittest import mock

import pytest

from src.models.note import Note
from src.repositories.note import NoteRepository

if TYPE_CHECKING:
    from src.services.note import NoteService


@pytest.fixture(scope="session")
def mock_note_repository(container) -> Generator[mock.Mock, None, None]:
    container.note_repository.override(mock.Mock(spec=NoteRepository))
    yield container.note_repository()
    container.note_repository.reset_override()


@pytest.fixture(scope="session")
def note_service(container) -> "NoteService":
    return container.note_service()


@pytest.fixture
def expected_notes_with() -> Callable:
    """
    Notes fabric, allow create one or more Notes with custom attributes

    Returns:
        Note | list[Note]
        if amount is 1, returns single Note instance
        else returns list of Notes according amount
    """

    def wrapper(
        id: uuid.UUID | None = None,
        title: str | None = None,
        content: str | None = None,
        owner_id: uuid.UUID | None = None,
        amount: int = 1,
    ) -> Note | list[Note]:
        if amount == 1:
            return Note(
                id=id or uuid.uuid4(),
                title=title or "some_expected_title",
                content=content or "# some expected md",
                owner_id=owner_id or uuid.uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        return [
            Note(
                id=uuid.uuid4(),
                title=f"{title or 'some_expected_title'}_{i}",
                content=f"{content or '# some expected md'}_{i}",
                owner_id=owner_id or uuid.uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            for i in range(1, amount + 1)
        ]

    return wrapper
