from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select

from models.auth import AuthCredentials
from exceptions.repositories import RowDoesNotExist, RowAlreadyExists


class AuthRepository:
    model = AuthCredentials

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine

    async def get_one_by_login(self, login: str) -> AuthCredentials:
        async with AsyncSession(self.engine) as session:
            query = select(self.model.login, self.model.password) \
                .where(self.model.login == login)
            result = await session.execute(query)

            try:
                credentials = result.scalar_one()
            except NoResultFound as e:
                raise RowDoesNotExist(
                    f'Unable to find row with login - {login}'
                ) from e
            
            return credentials

    async def create_one(self, credentials: AuthCredentials) -> int:
        async with AsyncSession(self.engine) as session:
            session.add(credentials)
            try:
                await session.flush()
                new_credentials_id = credentials.id
                await session.commit()
            except IntegrityError as e:
                raise RowAlreadyExists(
                    f'Row with login - {credentials.login} '
                    'already exists'
                ) from e

            return new_credentials_id
        
    async def delete_one(self, credentials: AuthCredentials):
        async with AsyncSession(self.engine) as session:
            await session.delete(credentials)
            await session.commit()
