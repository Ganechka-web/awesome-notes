from repositories.note import NoteRepository
from shemas.note import ( 
    NoteOutputShema, 
    NoteCreateShema
)
from models.note import Note
from exceptions.repository import DatabaseError, NoSuchRowError
from exceptions.service import NoteNotFoundError, NoteAlreadyExistsError


class NoteService:
    def __init__(self, repository: NoteRepository):
        self.repository = repository

    async def get_all(self) -> list[NoteOutputShema]:
        notes = await self.repository.get_all()

        return [NoteOutputShema.model_validate(note) for note in notes]

    async def get_all_by_owner_id(self, owner_id: int) -> list[NoteOutputShema]:
        notes_by_owner_id = (
            await self.repository.get_all_by_owner_id(owner_id=owner_id)
        )

        return [NoteOutputShema.model_validate(note) 
                for note in notes_by_owner_id]
    
    async def get_one_by_id(self, note_id: int) -> NoteOutputShema:
        try: 
            note = await self.repository.get_one_by_id(note_id=note_id)
        except NoSuchRowError as e:
            raise NoteNotFoundError(
                f'Unable to find note with id - {note_id}'
            ) from e

        return NoteOutputShema.model_validate(note)
    
    async def create_one(self, new_note: NoteCreateShema) -> int:
        new_note_orm = Note(**new_note.model_dump())
        try:
            new_note_id = await self.repository.create_one(note=new_note_orm)
        except DatabaseError as e:
            raise NoteAlreadyExistsError(
                f'Note with title - {new_note.title} already exists'
            ) from e

        return new_note_id
