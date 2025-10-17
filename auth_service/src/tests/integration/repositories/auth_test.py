import uuid
from typing import TYPE_CHECKING

import pytest

from src.exceptions.repositories import (
    RowDoesNotExist,
    RowAlreadyExists,
)

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository


class TestAuthRepository:
    @pytest.mark.asyncio
    async def test_get_one_by_login(
        self, expected_data_with, insert_test_data, auth_repository: "AuthRepository"
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
        id,
        login,
        is_exists,
        expected_data_with,
        insert_test_data,
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
        self, id, login, is_exists, auth_repository: "AuthRepository"
    ):
        result = await auth_repository.exists(id=id, login=login)

        assert result == is_exists

    @pytest.mark.asyncio
    async def test_create_one_success(
        self, expected_data_with, auth_repository: "AuthRepository"
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
        self, expected_data_with, insert_test_data, auth_repository: "AuthRepository"
    ):
        exp_credentials_orm, _ = expected_data_with(amount=1)
        await insert_test_data(exp_credentials_orm)
        same_exp_credentials_orm, _ = expected_data_with(amount=1)

        with pytest.raises(RowAlreadyExists):
            await auth_repository.create_one(credentials=same_exp_credentials_orm[0])

    @pytest.mark.asyncio
    async def test_delete_one_success(
        self, expected_data_with, insert_test_data, auth_repository: "AuthRepository"
    ):
        exp_credentials_orm, exp_credentials_attrs = expected_data_with(amount=1)
        await insert_test_data(exp_credentials_orm)

        await auth_repository.delete_one(exp_credentials_orm[0])

        with pytest.raises(RowDoesNotExist):
            _ = await auth_repository.get_one_by_login(
                login=exp_credentials_attrs[0]["login"]
            )
