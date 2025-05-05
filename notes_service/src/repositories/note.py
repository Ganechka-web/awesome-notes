from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select

from models.note import Note
from exceptions.repository import DatabaseError, NoSuchRowError


class NoteRepository:
    model = Note

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_all(self) -> list[Note]:
        async with AsyncSession(self.engine) as session:
            query = select(self.model)
            notes = await session.scalars(query)

            return notes.all()

    async def get_all_by_owner_id(self, owner_id: int) -> list[Note]:
        async with AsyncSession(self.engine) as session:
            query = select(self.model).where(self.model.owner_id == owner_id)
            notes_by_owner_id = await session.scalars(query)

            return notes_by_owner_id.all()
    
    async def get_one_by_id(self, note_id: int) -> Note:
        async with AsyncSession(self.engine) as session:
            query = select(self.model).where(self.model.id == note_id)
            note = await session.execute(query)
            try:
                return note.scalar_one()
            except NoResultFound as e:
                raise NoSuchRowError(
                    f'Unable to find row with id - {note_id}'
                ) from e
            
    async def create_one(self, note: Note) -> int:
        async with AsyncSession(self.engine) as session:
            session.add(note)

            try:
                await session.flush()
                new_note_id = note.id
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError(
                    'Error during saving row'
                ) from e

            return new_note_id    
