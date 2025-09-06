from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository


@pytest.mark.asyncio
class TestAuthRepository:
    @pytest.mark.usefixtures("insert_test_data")
    @pytest.mark.parametrize(
        ("login",), (("test_user_1",), ("test_user_2",), ("test_user_3",))
    )
    async def test_get_one_by_login(self, login: str, get_auth_repository: "AuthRepository"):
        auth_creadentials = await get_auth_repository.get_one_by_login(login=login)
        assert auth_creadentials.login == login
