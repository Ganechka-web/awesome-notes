from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select

from models.note import Note
from exceptions.repository import DatabaseError, NoSuchRowError
from repositories.specifications import Specification


class NoteRepository:
    model = Note

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_all(self) -> list[Note]:
        async with AsyncSession(self.engine) as session:
            query = select(self.model)
            notes = await session.scalars(query)

            return notes.all()
        
    async def filter_by(self, specification: Specification) -> list[Note]: 
        async with AsyncSession(self.engine) as session:
            query = select(self.model).where(*specification.is_satisfied())
            filtered_notes = await session.scalars(query)

            return filtered_notes.all()
    
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

    async def update_one(self, note: Note) -> None:
        async with AsyncSession(self.engine) as session:
            session.add(note)

            try: 
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError(
                    'Error during saving row'
                ) from e
    
    async def delete_one(self, note: Note) -> None:
        async with AsyncSession(self.engine) as session:
            await session.delete(note)
            await session.commit()
    