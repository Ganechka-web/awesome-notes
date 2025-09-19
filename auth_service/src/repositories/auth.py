from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.exc import NoResultFound, IntegrityError, DBAPIError
from sqlalchemy import select, exists, or_

from src.models.auth import AuthCredentials
from src.exceptions.repositories import RowDoesNotExist, RowAlreadyExists, ColumnContentTooLongError

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase


class AuthRepository:
    model = AuthCredentials

    def __init__(self, database: "AsyncDatabase") -> None:
        self.db = database

    async def get_one_by_login(self, login: str) -> AuthCredentials:
        async with self.db.get_session() as session:
            query = select(AuthCredentials).where(
                self.model.login == login
            )
            result = await session.scalars(query)
            try:
                credentials = result.one()
            except NoResultFound as e:
                raise RowDoesNotExist(f"Unable to find row with {login=}") from e
            return credentials
        
    async def exists(self, id: UUID | None = None, login: str | None = None) -> bool:
        async with self.db.get_session() as session:
            if not any([id, login]):
                return False
            
            query = select(exists().where(
                or_(
                    *(clause for clause in 
                        [self.model.id == id if id else None,
                        self.model.login == login if login else None]  
                        if clause is not None
                    )
                )
            ))
            result = await session.execute(query)

            return bool(result.scalar())

    async def create_one(self, credentials: AuthCredentials) -> UUID:
        async with self.db.get_session() as session:
            session.add(credentials)
            try:
                await session.flush()
                new_credentials_id = credentials.id
                await session.commit()
            except IntegrityError as e:
                raise RowAlreadyExists(
                    f"Row with login - {credentials.login} already exists"
                ) from e
            except DBAPIError as e:
                raise ColumnContentTooLongError(
                    f"Column login - {credentials.login} too long"
                ) from e

            return new_credentials_id

    async def delete_one(self, credentials: AuthCredentials):
        async with self.db.get_session() as session:
            await session.delete(credentials)
            await session.commit()
