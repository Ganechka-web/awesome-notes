import uuid
from typing import TYPE_CHECKING

from sqlalchemy.exc import NoResultFound, SQLAlchemyError, IntegrityError
from sqlalchemy import select, exists, or_, false
from asyncpg.exceptions import UniqueViolationError

from src.exceptions.repositories import NoSuchRowError, DataBaseError, RowAlreadyExists
from src.models.user import User
from src.logger import logger

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase


class UserRepository:
    model = User

    def __init__(self, database: "AsyncDatabase"):
        self.db = database

    async def get_all(self) -> list[User]:
        async with self.db.get_session() as session:
            try:
                query = select(User)
                users = await session.scalars(query)

                return users.all()
            
            except SQLAlchemyError as e:
                await session.rollback()
                logger.warning(
                    "There is an unexpected error during working with session, "
                    f"err class - {e.__class__}, err info - {e._message()}"
                )
                raise DataBaseError("...")

    async def get_one_by_id(self, id: uuid.UUID) -> User:
        async with self.db.get_session() as session:
            query = select(self.model).where(self.model.id == id)
            user = await session.execute(query)

            try:
                return user.scalar_one()
            except NoResultFound as e:
                raise NoSuchRowError(f"No such row with id - {id}") from e
            except SQLAlchemyError as e:
                await session.rollback()
                logger.warning(
                    "There is an unexpected error during working with session, "
                    f"err class - {e.__class__}, err info - {e._message()}"
                )
                raise DataBaseError("...")

    async def get_one_by_username(self, username: str) -> User | None:
        async with self.db.get_session() as session:
            try:
                query = select(self.model).where(self.model.username == username)
                user = await session.execute(query)

                return user.scalar_one()
            
            except NoResultFound as e:
                raise NoSuchRowError(f"No such row with  username - {username}") from e
            except SQLAlchemyError as e:
                await session.rollback()
                logger.warning(
                    "There is an unexpected error during working with session, "
                    f"err class - {e.__class__}, err info - {e._message()}"
                )
                raise DataBaseError("...")

    async def exists(
        self, id: uuid.UUID | None = None, username: str | None = None
    ) -> bool:
        if not any([id, username]):
            return False

        async with self.db.get_session() as session:
            try:
                query = select(
                    exists().where(
                        or_(
                            false(),
                            *[
                                clause
                                for clause in (
                                    (self.model.id == id) if id else None,
                                    (self.model.username == username) if username else None,
                                )
                                if clause is not None
                            ],
                        )
                    )
                )
                result = await session.execute(query)
                return bool(result.scalar_one())
            except SQLAlchemyError as e:
                await session.rollback()
                logger.warning(
                    "There is an unexpected error during working with session, "
                    f"err class - {e.__class__}, err info - {e._message()}"
                )
                raise DataBaseError("...")

    async def create_one(self, user: User) -> uuid.UUID:
        async with self.db.get_session() as session:
            try:
                session.add(user)
                await session.flush()
                new_user_id = user.id
                await session.commit()

                return new_user_id

            except IntegrityError as e:
                await session.rollback()
                if e.orig == UniqueViolationError:
                    logger.warning(f"Unable to save row detail - {e.detail}")
                    raise RowAlreadyExists("Row with same fields already exists")
                else:
                    logger.error(
                        "There is an unexpected error during saving row",
                        extra={"e_class": e.__class__, "e_info": str(e)},
                    )
                    raise DataBaseError("...")

    async def update_one(self, user: User) -> None:
        async with self.db.get_session() as session:
            try:
                session.add(user)
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                if e.orig == UniqueViolationError:
                    logger.warning(f"Unable to save row detail - {e.detail}")
                    raise RowAlreadyExists("Row with same fields already exists")
                else:
                    logger.warning(
                        "There is an unexpected error during working with session, "
                        f"err class - {e.__class__}, err info - {e._message()}"
                    )
                    raise DataBaseError("...")

    async def delete_one(self, user: User) -> None:
        async with self.db.get_session() as session:
            try:
                await session.delete(user)
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                logger.warning(
                    "There is an unexpected error during working with session, "
                    f"err class - {e.__class__}, err info - {e._message()}"
                )
                raise DataBaseError("...")