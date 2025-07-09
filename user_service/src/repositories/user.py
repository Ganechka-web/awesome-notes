from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy import select

from core.database import AsyncDatabase
from exceptions.repositories import DataBaseError
from models.user import User


class UserRepository:
    model = User

    def __init__(self, database: AsyncDatabase):
        self.db = database

    async def get_all(self) -> list[User]:
        async with self.db.get_session() as session:
            query = select(User)
            users = await session.scalars(query)

            return users.all()

    async def get_one_by_id(self, id: str) -> User:
        async with self.db.get_session() as session:
            query = select(User).where(self.model.id == id)
            user = await session.execute(query)

            try:
                return user.scalar_one()
            except NoResultFound as e:
                raise DataBaseError(f"No such row id - {id}") from e

    async def get_one_by_username(self, username: str) -> User:
        async with self.db.get_session() as session:
            query = select(self.model).where(self.model.username == username)
            user = await session.execute(query)

            try:
                return user.scalar_one()
            except NoResultFound as e:
                raise DataBaseError(f"No such row username - {username}") from e

    async def create_one(self, user: User) -> str:
        async with self.db.get_session() as session:
            session.add(user)
            try:
                await session.flush()
                new_user_id = user.id
                await session.commit()
            except IntegrityError as e:
                raise DataBaseError("Error during user saving") from e

            return new_user_id

    async def update_one(self, user: User) -> None:
        async with self.db.get_session() as session:
            session.add(user)
            try:
                await session.commit()
            except IntegrityError as e:
                raise DataBaseError("Error during updating user") from e

    async def delete_one(self, user: User) -> None:
        async with self.db.get_session() as session:
            await session.delete(user)
            await session.commit()
