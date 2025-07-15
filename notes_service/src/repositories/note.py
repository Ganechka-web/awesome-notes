from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select, delete

from models.note import Note
from exceptions.repository import DatabaseError, NoSuchRowError
from repositories.specifications import Specification

if TYPE_CHECKING:
    from core.database import AsyncDatabase


class NoteRepository:
    model = Note

    def __init__(self, database: "AsyncDatabase"):
        self.db = database

    async def get_all(self) -> list[Note]:
        async with self.db.get_session() as session:
            query = select(self.model)
            notes = await session.scalars(query)

            return notes.all()

    async def filter_by(self, specification: Specification) -> list[Note]:
        async with self.db.get_session() as session:
            query = select(self.model).where(*specification.is_satisfied())
            filtered_notes = await session.scalars(query)

            return filtered_notes.all()

    async def get_one_by_id(self, note_id: UUID) -> Note:
        async with self.db.get_session() as session:
            query = select(self.model).where(self.model.id == note_id)
            note = await session.execute(query)
            try:
                return note.scalar_one()
            except NoResultFound as e:
                raise NoSuchRowError(f"Unable to find row with id - {note_id}") from e

    async def create_one(self, note: Note) -> int:
        async with self.db.get_session() as session:
            session.add(note)

            try:
                await session.flush()
                new_note_id = note.id
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError("Error during saving row") from e

            return new_note_id

    async def update_one(self, note: Note) -> None:
        async with self.db.get_session() as session:
            session.add(note)

            try:
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise DatabaseError("Error during saving row") from e

    async def delete_one(self, note: Note) -> None:
        async with self.db.get_session() as session:
            await session.delete(note)
            await session.commit()

    async def delete_all(self, note_ids: list[UUID]) -> None:
        async with self.db.get_session() as session:
            query = delete(self.model).where(self.model.id.in_(note_ids))
            await session.execute(query)
            await session.commit()
