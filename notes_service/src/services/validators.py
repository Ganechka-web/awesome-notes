# Contains NoteService validators 
from abc import ABC, abstractmethod

from repositories.specifications import NotesForOwnerSpecification
from repositories.note import NoteRepository
from exceptions.service import NoteAlreadyExistsError


class Validator(ABC):
    @abstractmethod
    def validate(self):
        raise NotImplementedError()


class NoteTitleUniqueForOwnerValidator(Validator):
    """Validates note title for owner"""
    def __init__(self, repository: NoteRepository, owner_id: int) -> None:
        self.notes_for_owner_spec = NotesForOwnerSpecification
        self.repository = repository
        self.owner_id = owner_id

    async def validate(self, new_note_title: str) -> None:
        specification = self.notes_for_owner_spec(owner_id=self.owner_id)
        notes_for_owner = await self.repository.filter_by(specification=specification)
        
        notes_titles_for_owner = {note.title for note in notes_for_owner}
        if new_note_title in notes_titles_for_owner:
            raise NoteAlreadyExistsError(
                f'Note with title {new_note_title} already exists '
                f'for owner owner_id - {self.owner_id}'
            )   
        