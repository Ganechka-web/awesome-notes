from typing import TYPE_CHECKING, Generator, Callable
from unittest import mock
from datetime import datetime
import uuid

import pytest

from src.schemas.note import NoteOutputShema

if TYPE_CHECKING:
    from src.services.note import NoteService


@pytest.fixture(scope="module")
def mock_note_service(container) -> Generator["NoteService", None, None]:
    origin_provider = container.note_service
    container.note_service.override(mock.Mock())
    yield container.note_service()
    origin_provider.reset_override()


@pytest.fixture
def expected_notes_sch_with() -> Callable:
    def wrapper(
        id: uuid.UUID | None = None,
        title: str | None = None,
        content: str | None = None,
        owner_id: uuid.UUID | None = None,
        amount: int = 1,
    ) -> list[NoteOutputShema] | NoteOutputShema:
        if amount == 1:
            return NoteOutputShema(
                id=id or uuid.uuid4(),
                title=title or "expected_title_1",
                content=content or "# expected md content",
                owner_id=owner_id or uuid.uuid4(),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        notes_sch = []
        for i in range(1, amount + 1):
            notes_sch.append(
                NoteOutputShema(
                    id=id or uuid.uuid4(),
                    title=title or f"expected_title_{i}",
                    content=content or f"# expected md content {i}",
                    owner_id=owner_id or uuid.uuid4(),
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
            )
        return notes_sch

    return wrapper
