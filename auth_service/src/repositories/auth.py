import uuid
from datetime import timedelta
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select, exists, or_

from src.models.auth import AuthCredentials
from src.exceptions.repositories import (
    RowDoesNotExist,
    RowAlreadyExists,
    TokenDoesNotExists,
)

if TYPE_CHECKING:
    from src.core.database import AsyncDatabase
    from src.core.redis import AsyncRedis


class Repository(ABC):
    """Abstract class for repoisitories"""


class TokenRepository(Repository):
    """Abstract class for working with tokens"""

    @abstractmethod
    async def save_token(self, key: str, token: str, ttl: int | timedelta) -> None:
        pass

    @abstractmethod
    async def get_token(self, key: str) -> str:
        pass

    @abstractmethod
    async def is_token_exists(self, key: str) -> bool:
        pass

    @abstractmethod
    async def delete_token(self, key: str) -> None:
        pass


class AuthRepository(Repository):
    model = AuthCredentials

    def __init__(self, database: "AsyncDatabase") -> None:
        self.db = database

    async def get_one_by_login(self, login: str) -> AuthCredentials:
        async with self.db.get_session() as session:
            query = select(AuthCredentials).where(self.model.login == login)
            result = await session.scalars(query)
            try:
                credentials = result.one()
            except NoResultFound as e:
                raise RowDoesNotExist(f"Unable to find row with {login=}") from e
            return credentials

    async def exists(
        self, id: uuid.UUID | None = None, login: str | None = None
    ) -> bool:
        async with self.db.get_session() as session:
            if not any([id, login]):
                return False

            query = select(
                exists().where(
                    or_(
                        *(
                            clause
                            for clause in [
                                self.model.id == id if id else None,
                                self.model.login == login if login else None,
                            ]
                            if clause is not None
                        )
                    )
                )
            )
            result = await session.execute(query)

            return bool(result.scalar())

    async def create_one(self, credentials: AuthCredentials) -> uuid.UUID:
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


class RedisTokenRepository(TokenRepository):
    """TokenRepository implementaion for Redis key-value storage"""

    def __init__(self, auth_redis: "AsyncRedis") -> None:
        self.auth_redis = auth_redis

    def _key(self, key: str) -> str:
        """Formats and returns key"""
        return f"refresh_token:{key}"

    async def save_token(self, key: str, token: str, ttl: int | timedelta) -> None:
        await self.auth_redis.r.setex(self._key(key), ttl, token)

    async def get_token(self, key: str) -> str:
        key = self._key(key)
        token = await self.auth_redis.r.get(key)

        if token is None:
            raise TokenDoesNotExists(f"Unable to get token with key - {key}")
        return token

    async def is_token_exists(self, key: str) -> bool:
        return bool(await self.auth_redis.r.exists(self._key(key)))

    async def delete_token(self, key: str) -> None:
        await self.auth_redis.r.delete(self._key(key))
