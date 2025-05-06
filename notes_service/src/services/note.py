from repositories.note import NoteRepository
from repositories.specifications import NotesForOwnerSpecification
from models.note import Note
from shemas.note import ( 
    NoteOutputShema, 
    NoteCreateShema
)
from services.validators import NoteTitleUniqueForOwnerValidator
from exceptions.repository import NoSuchRowError
from exceptions.service import NoteNotFoundError
    

class NoteService:
    def __init__(self, repository: NoteRepository):
        self.notes_for_owner_spec = NotesForOwnerSpecification
        self.note_title_unique_for_owner_validator = NoteTitleUniqueForOwnerValidator
        self.repository = repository

    async def get_all(self) -> list[NoteOutputShema]:
        notes = await self.repository.get_all()

        return [NoteOutputShema.model_validate(note) for note in notes]

    async def get_all_by_owner_id(self, owner_id: int) -> list[NoteOutputShema]:
        specification = self.notes_for_owner_spec(owner_id=owner_id)
        notes_by_owner_id = (
            await self.repository.filter_by(specification=specification)
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

        note_title_unique_for_owner_validator = self.note_title_unique_for_owner_validator(
            repository=self.repository, 
            owner_id=Note.owner_id
        )
        await note_title_unique_for_owner_validator.validate(new_note_title=new_note.title)

        new_note_id = await self.repository.create_one(note=new_note_orm)

        return new_note_id
