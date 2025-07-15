# Contains NoteRepository specifications
from abc import ABC, abstractmethod
from uuid import UUID

from models.note import Note


class Specification(ABC):
    @abstractmethod
    def is_satisfied(self):
        raise NotImplementedError()


class NotesForOwnerSpecification(Specification):
    """specification for filter notes by owner_id"""

    def __init__(self, owner_id: UUID) -> None:
        self.owner_id = owner_id

    def is_satisfied(self) -> tuple:
        return (Note.owner_id == self.owner_id,)
