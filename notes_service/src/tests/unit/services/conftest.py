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
def expected_notes_orm() -> list[Note]:
    return [
        Note(
            id=uuid.uuid4(),
            title="test_note_title",
            content="# Markdown title\n\n - list item 1\n - list item 2",
            owner_id=uuid.uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Note(
            id=uuid.uuid4(),
            title="test_note_title_2",
            content="Just plain text",
            owner_id=uuid.uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Note(
            id=uuid.uuid4(),
            title="test_note_title_3",
            content="Some link in markdown format [https://www.google.com][google.com]",
            owner_id=uuid.uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


@pytest.fixture
def expected_notes_orm_with_same_ids() -> Callable:
    def wrapper(owner_id: uuid.UUID) -> list[Note]:
        return [
            Note(
                id=uuid.uuid4(),
                title="test_note_title",
                content="# Markdown title\n\n - list item 1\n - list item 2",
                owner_id=owner_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
            Note(
                id=uuid.uuid4(),
                title="test_note_title_3",
                content="Some link in markdown format [https://www.google.com][google.com]",
                owner_id=owner_id,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            ),
        ]

    return wrapper


@pytest.fixture
def expected_note_with() -> Callable:
    def wrapper(
        id: uuid.UUID | None = None,
        title: str | None = None,
        content: str | None = None,
        owner_id: uuid.UUID | None = None,
    ) -> Note:
        return Note(
            id=id or uuid.uuid4(),
            title=title or "expected_title",
            content=content or "# Some expected markdow\n\n - expected item",
            owner_id=owner_id or uuid.uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    return wrapper
