from typing import TYPE_CHECKING

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select

from models.auth import AuthCredentials
from exceptions.repositories import RowDoesNotExist, RowAlreadyExists

if TYPE_CHECKING:
    from core.database import AsyncDatabase


class AuthRepository:
    model = AuthCredentials

    def __init__(self, database: "AsyncDatabase") -> None:
        self.db = database

    async def get_one_by_login(self, login: str) -> AuthCredentials:
        async with self.db.get_session() as session:
            query = select(self.model.login, self.model.password).where(
                self.model.login == login
            )
            result = await session.execute(query)

            try:
                credentials = result.scalar_one()
            except NoResultFound as e:
                raise RowDoesNotExist(f"Unable to find row with login - {login}") from e

            return credentials

    async def create_one(self, credentials: AuthCredentials) -> int:
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

            return new_credentials_id

    async def delete_one(self, credentials: AuthCredentials):
        async with self.db.get_session() as session:
            await session.delete(credentials)
            await session.commit()
