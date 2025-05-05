from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import select

from exceptions.repositories import DataBaseError
from models.user import User


class UserRepository:
    model = User

    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def get_all(self) -> list[User]:
        async with AsyncSession(self.engine) as session:
            query = select(User)
            users = await session.scalars(query)

            return users.all()

    async def get_one_by_id(self, id: int) -> User:
        async with AsyncSession(self.engine) as session:
            query = select(User).where(self.model.id == id)
            user = await session.execute(query)

            try:
                return user.scalar_one()
            except NoResultFound as e:
                raise DataBaseError(
                    f'No such row id - {id}'
                ) from e

    async def get_one_by_username(self, username: str) -> User:
        async with AsyncSession(self.engine) as session:
            query = select(self.model).where(self.model.username == username)
            user = await session.execute(query)

            try:
                return user.scalar_one()
            except NoResultFound as e:
                raise DataBaseError(
                    f'No such row username - {username}'
                ) from e

    async def create_one(self, user: User) -> int:
        async with AsyncSession(self.engine) as session:
            session.add(user)
            try:
                await session.flush()
                new_user_id = user.id
                await session.commit()
            except IntegrityError as e:
                raise DataBaseError(
                    'Error during user saving'  
                ) from e 

            return new_user_id
        
    async def update_one(self, user: User) -> None:
        async with AsyncSession(self.engine) as session:
            session.add(user)
            try:
                await session.commit()
            except IntegrityError as e:
                raise DataBaseError(
                    "Error during updating user"
                ) from e
    
    async def delete_one(self, user: User) -> None:
        async with AsyncSession(self.engine) as session:
            await session.delete(user)
            await session.commit()