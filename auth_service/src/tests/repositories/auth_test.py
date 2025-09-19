from typing import TYPE_CHECKING
from uuid import UUID
from contextlib import nullcontext as does_not_raise
from unittest import mock

import pytest

from src.models.auth import AuthCredentials
from src.exceptions.repositories import (
    RowDoesNotExist,
    RowAlreadyExists,
    ColumnContentTooLongError,
)

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository


class TestAuthRepository:
    @pytest.mark.parametrize(
        ("login", "expected_login", "exception"),
        (
            ("test_user_1", "test_user_1", does_not_raise()),
            ("test_user_2", "test_user_2", does_not_raise()),
            ("test_unexistent_user", None, pytest.raises(RowDoesNotExist)),
        ),
    )
    @pytest.mark.asyncio
    async def test_get_one_by_login(
        self, login, expected_login, exception, auth_repository: "AuthRepository"
    ):
        with exception:
            credentials = await auth_repository.get_one_by_login(login=login)

            assert credentials.login == expected_login

    @pytest.mark.parametrize(
        ("login", "password", "exception"),
        (
            ("creation_test_1", "some@password@hash", does_not_raise()),
            ("creation_log_test_1", "some@password@hash", does_not_raise()),
            (
                "creation_too_long_login_test_2",
                "1233@klxmk@",
                pytest.raises(ColumnContentTooLongError),
            ),
            ("creation_test_1", "jj22k2kk", pytest.raises(RowAlreadyExists)),
        ),
    )
    @pytest.mark.asyncio
    async def test_create_one(
        self, login, password, exception, auth_repository: "AuthRepository"
    ):
        with exception:
            auth_credentials = AuthCredentials(login=login, password=password)
            auth_credentials_id = await auth_repository.create_one(
                credentials=auth_credentials
            )
            created_auth_credentials = await auth_repository.get_one_by_login(
                login=login
            )

            assert isinstance(auth_credentials_id, UUID) is True
            assert login == created_auth_credentials.login
            assert password == created_auth_credentials.password

    @pytest.mark.parametrize(
        ("login", "exception"),
        (("test_user_1", does_not_raise()), ("test_user_2", does_not_raise())),
    )
    @pytest.mark.asyncio
    async def test_delete_one(
        self, login, exception, auth_repository: "AuthRepository"
    ):
        with exception:
            auth_credentials_on_delete = await auth_repository.get_one_by_login(
                login=login
            )

            auth_repository.db.session.delete = mock.AsyncMock()
            auth_repository.db.session.commit = mock.AsyncMock()

            await auth_repository.delete_one(credentials=auth_credentials_on_delete)

            auth_repository.db.session.delete.assert_awaited_once_with(
                auth_credentials_on_delete
            )
            auth_repository.db.session.commit.assert_awaited_once()
