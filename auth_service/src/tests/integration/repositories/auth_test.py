import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable

import pytest

from src.exceptions.repositories import (
    RowDoesNotExist,
    RowAlreadyExists,
    TokenDoesNotExists,
)

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository, RedisTokenRepository


class TestAuthRepository:
    @pytest.mark.asyncio
    async def test_get_one_by_login(
        self,
        expected_data_with: Callable,
        insert_test_data: Callable,
        auth_repository: "AuthRepository",
    ):
        expected_credentials_orm, expected_credentials_attrs = expected_data_with(
            login="some_expected_login"
        )
        await insert_test_data(expected_credentials_orm)

        credentials = await auth_repository.get_one_by_login(
            login=expected_credentials_attrs[0]["login"]
        )

        assert credentials.login == expected_credentials_attrs[0]["login"]

    @pytest.mark.asyncio
    async def test_get_one_by_login_unexists(self, auth_repository: "AuthRepository"):
        unexisted_login = "some_unexisted_login"

        with pytest.raises(RowDoesNotExist):
            await auth_repository.get_one_by_login(login=unexisted_login)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("id", "login", "is_exists"),
        (
            (uuid.uuid4(), "some_login", True),
            (uuid.uuid4(), None, True),
            (None, "existed_login", True),
        ),
    )
    async def test_exists(
        self,
        id: uuid.UUID,
        login: str,
        is_exists: bool,
        expected_data_with: Callable,
        insert_test_data: Callable,
        auth_repository: "AuthRepository",
    ):
        exp_credentials_orm, _ = expected_data_with(id=id, login=login, amount=1)
        await insert_test_data(exp_credentials_orm)

        result = await auth_repository.exists(id=id, login=login)

        assert result == is_exists

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("id", "login", "is_exists"),
        (
            (uuid.uuid4(), "some_login", False),
            (uuid.uuid4(), None, False),
            (None, "existed_login", False),
        ),
    )
    async def test_exists_unexists(
        self,
        id: uuid.UUID,
        login: str,
        is_exists: bool,
        auth_repository: "AuthRepository",
    ):
        result = await auth_repository.exists(id=id, login=login)

        assert result == is_exists

    @pytest.mark.asyncio
    async def test_create_one_success(
        self, expected_data_with: Callable, auth_repository: "AuthRepository"
    ):
        exp_credentials_orm, exp_credentials_attrs = expected_data_with(amount=1)

        new_credentials_id = await auth_repository.create_one(
            credentials=exp_credentials_orm[0]
        )
        assert isinstance(new_credentials_id, uuid.UUID)

        created_credentials = await auth_repository.get_one_by_login(
            login=exp_credentials_attrs[0]["login"]
        )
        assert created_credentials.login == exp_credentials_attrs[0]["login"]
        assert created_credentials.password == exp_credentials_attrs[0]["password"]

    @pytest.mark.asyncio
    async def test_create_one_already_exists(
        self,
        expected_data_with: Callable,
        insert_test_data: Callable,
        auth_repository: "AuthRepository",
    ):
        exp_credentials_orm, _ = expected_data_with(amount=1)
        await insert_test_data(exp_credentials_orm)
        same_exp_credentials_orm, _ = expected_data_with(amount=1)

        with pytest.raises(RowAlreadyExists):
            await auth_repository.create_one(credentials=same_exp_credentials_orm[0])

    @pytest.mark.asyncio
    async def test_delete_one_success(
        self,
        expected_data_with: Callable,
        insert_test_data: Callable,
        auth_repository: "AuthRepository",
    ):
        exp_credentials_orm, exp_credentials_attrs = expected_data_with(amount=1)
        await insert_test_data(exp_credentials_orm)

        await auth_repository.delete_one(exp_credentials_orm[0])

        with pytest.raises(RowDoesNotExist):
            _ = await auth_repository.get_one_by_login(
                login=exp_credentials_attrs[0]["login"]
            )


class TestRedisTokenRepository:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("ttl", "payload"),
        (
            (
                timedelta(minutes=10),
                {
                    "sub": "Some_sub",
                    "exp": datetime.now().replace(microsecond=0)
                    + timedelta(minutes=10),
                },
            ),
            (
                timedelta(days=1),
                {
                    "sub": "Some_another_sub",
                    "exp": datetime.now().replace(microsecond=0) + timedelta(days=1),
                },
            ),
        ),
    )
    async def test_save_token(
        self,
        ttl: int,
        payload: dict[str, Any],
        encode_test_token: Callable,
        decode_test_token: Callable,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = payload["sub"]
        token = encode_test_token(payload)

        await redis_token_repository.save_token(key, token, ttl)

        saved_token = await redis_token_repository.get_token(key)
        assert saved_token == token
        saved_token_payload = decode_test_token(saved_token)

        # Tokens tz=timezone.utc
        saved_token_payload["exp"] = datetime.fromtimestamp(
            saved_token_payload["exp"], tz=timezone.utc
        ).replace(tzinfo=None)
        assert saved_token_payload == payload

    @pytest.mark.asyncio
    async def test_get_token(
        self,
        encode_test_token: Callable,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"
        prepared_token = encode_test_token(
            {"sub": key, "exp": datetime.now(tz=timezone.utc)}
        )
        await redis_token_repository.save_token(
            key, prepared_token, timedelta(minutes=10)
        )

        token = await redis_token_repository.get_token(key)
        assert token == prepared_token

    @pytest.mark.asyncio
    async def test_get_token_unexists(
        self,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"

        with pytest.raises(TokenDoesNotExists):
            _ = await redis_token_repository.get_token(key)

    @pytest.mark.asyncio
    async def test_is_token_exists(
        self,
        encode_test_token: Callable,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"
        prepared_token = encode_test_token(
            {"sub": key, "exp": datetime.now(tz=timezone.utc)}
        )
        await redis_token_repository.save_token(
            key, prepared_token, timedelta(minutes=10)
        )

        result = await redis_token_repository.is_token_exists(key)
        assert result

    @pytest.mark.asyncio
    async def test_is_token_exists_unexists(
        self,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"

        result = await redis_token_repository.is_token_exists(key)
        assert not result

    @pytest.mark.asyncio
    async def test_delete_token(
        self,
        encode_test_token: Callable,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"
        token = encode_test_token({"sub": key, "exp": datetime.now(tz=timezone.utc)})
        await redis_token_repository.save_token(key, token, timedelta(days=1))

        await redis_token_repository.delete_token(key)

        is_exists = await redis_token_repository.is_token_exists(key)
        assert not is_exists
        
    @pytest.mark.asyncio
    async def test_delete_token_unexists(
        self,
        redis_token_repository: "RedisTokenRepository",
    ):
        key = "Some_sub"

        await redis_token_repository.delete_token(key)

        is_exists = await redis_token_repository.is_token_exists(key)
        assert not is_exists

