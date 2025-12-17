import uuid
import json
from unittest import mock
from typing import TYPE_CHECKING, Callable

import pytest

from src.shemas.user import UserOutputShema, UserCreateShema, UserUpgrateShema
from src.exceptions.repositories import NoSuchRowError, RowAlreadyExists
from src.exceptions.services import UserNotFoundError, UserAlreadyExistsError
from src.exceptions.broker import UnableToConnectToBrokerError

if TYPE_CHECKING:
    from src.services.user import UserService


class TestUserService:
    @pytest.mark.asyncio
    async def test_get_all(
        self,
        mock_user_repository: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        exp_users_amount = 10
        exp_users_orm = expected_users_orm_with(amount=exp_users_amount)
        mock_user_repository.get_all = mock.AsyncMock(return_value=exp_users_orm)

        users = await user_service.get_all()

        mock_user_repository.get_all.assert_awaited_once()
        assert len(users) == exp_users_amount and all(
            map(lambda u: isinstance(u, UserOutputShema), users)
        )
        for uo, us in zip(exp_users_orm, users):
            assert uo.id == us.id
            assert uo.username == us.username
            assert uo.gender.value == us.gender
            assert uo.age == us.age
            assert uo.joined_at == us.joined_at
            assert uo.updated_at == us.updated_at

    @pytest.mark.asyncio
    async def test_get_one_by_id_success(
        self,
        mock_user_repository: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        exp_user_id = uuid.uuid4()
        exp_user_orm = expected_users_orm_with(id=exp_user_id, amount=1)
        mock_user_repository.get_one_by_id = mock.AsyncMock(return_value=exp_user_orm)

        user = await user_service.get_one_by_id(id=exp_user_id)

        mock_user_repository.get_one_by_id.assert_awaited_once_with(id=exp_user_id)
        assert isinstance(user, UserOutputShema)
        assert user.id == exp_user_id

    @pytest.mark.asyncio
    async def test_get_one_by_id_unexists(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        exp_user_id = uuid.uuid4()
        mock_user_repository.get_one_by_id = mock.AsyncMock(
            side_effect=[NoSuchRowError("...")]
        )

        with pytest.raises(UserNotFoundError):
            _ = await user_service.get_one_by_id(id=exp_user_id)

            mock_user_repository.get_one_by_id.assert_awaited_once_with(id=exp_user_id)

    @pytest.mark.asyncio
    async def test_get_one_by_username_success(
        self,
        mock_user_repository: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        exp_user_username = "some_test_username"
        exp_user_orm = expected_users_orm_with(username=exp_user_username, amount=1)
        mock_user_repository.get_one_by_username = mock.AsyncMock(
            return_value=exp_user_orm
        )

        user = await user_service.get_one_by_username(username=exp_user_username)

        mock_user_repository.get_one_by_username.assert_awaited_once_with(
            username=exp_user_username
        )
        assert isinstance(user, UserOutputShema)
        assert user.username == exp_user_username

    @pytest.mark.asyncio
    async def test_get_one_by_username_unexists(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        exp_user_username = "some_unexists_username"
        mock_user_repository.get_one_by_username = mock.AsyncMock(
            side_effect=[NoSuchRowError("...")]
        )

        with pytest.raises(UserNotFoundError):
            _ = await user_service.get_one_by_username(username=exp_user_username)

            mock_user_repository.get_one_by_username.assert_awaited_once_with(
                username=exp_user_username
            )

    @pytest.mark.asyncio
    async def test_create_one_success(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        exp_user_id = uuid.uuid4()
        exp_user_sch = UserCreateShema(username="New_username", gender="male", age=23)

        mock_user_repository.create_one = mock.AsyncMock(return_value=exp_user_id)

        created_user_id = await user_service.create_one(new_user=exp_user_sch)

        assert created_user_id == exp_user_id

        mock_user_repository.create_one.assert_awaited_once()
        called_user_orm = mock_user_repository.create_one.call_args.kwargs["user"]
        assert called_user_orm.username == exp_user_sch.username
        assert called_user_orm.gender == exp_user_sch.gender
        assert called_user_orm.age == exp_user_sch.age

    @pytest.mark.asyncio
    async def test_create_one_already_exists(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        exp_user_sch = UserCreateShema(
            username="Existed_username", gender="male", age=23
        )

        mock_user_repository.create_one = mock.AsyncMock(
            side_effect=[RowAlreadyExists("...")]
        )

        with pytest.raises(UserAlreadyExistsError):
            _ = await user_service.create_one(new_user=exp_user_sch)

            mock_user_repository.create_one.assert_awaited_once()
            called_user_orm = mock_user_repository.create_one.call_args.kwargs["user"]
            assert called_user_orm.username == exp_user_sch.username
            assert called_user_orm.gender == exp_user_sch.gender
            assert called_user_orm.age == exp_user_sch.age

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("username", "gender", "age"),
        (
            ("New_username", "male", 67),  # full entity update
            ("New_username", None, None),  # only username update
            (None, "female", None),  # only gender update
            (None, None, 26),  # only age update
        ),
    )
    async def test_update_one_success(
        self,
        username,
        gender,
        age,
        mock_user_repository: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        usr_on_update_id = uuid.uuid4()
        usr_on_update_orm = expected_users_orm_with(id=usr_on_update_id, amount=1)
        usr_on_update_sch = UserUpgrateShema(
            username=username if username else None,
            gender=gender if gender else None,
            age=age if age else None,
        )

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            return_value=usr_on_update_orm
        )
        mock_user_repository.update_one = mock.AsyncMock()

        await user_service.update_one(
            id=usr_on_update_id, updated_user=usr_on_update_sch
        )

        mock_user_repository.get_one_by_id.assert_awaited_once_with(id=usr_on_update_id)
        mock_user_repository.update_one.assert_awaited_once()

        called_user_orm = mock_user_repository.update_one.call_args.kwargs["user"]
        if usr_on_update_sch.username:
            assert called_user_orm.username == usr_on_update_sch.username
        if usr_on_update_sch.gender:
            assert called_user_orm.gender == usr_on_update_sch.gender
        if usr_on_update_sch.age:
            assert called_user_orm.age == usr_on_update_sch.age

    @pytest.mark.asyncio
    async def test_update_one_unexists(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        usr_on_update_id = uuid.uuid4()
        usr_on_update_sch = UserUpgrateShema(username="updated_username")

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            side_effect=[NoSuchRowError("...")]
        )

        with pytest.raises(UserNotFoundError):
            await user_service.update_one(
                id=usr_on_update_id, updated_user=usr_on_update_sch
            )

            mock_user_repository.get_one_by_id.assert_awaited_once_with(
                id=usr_on_update_id
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("username", "gender", "age"),
        (
            ("New_username", "male", 67),  # full entity update
            ("New_username", None, None),  # only username update
            (None, "female", None),  # only gender update
            (None, None, 26),  # only age update
        ),
    )
    async def test_update_one_already_exists(
        self,
        username,
        gender,
        age,
        mock_user_repository: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        usr_on_update_id = uuid.uuid4()
        usr_on_update_orm = expected_users_orm_with(id=usr_on_update_id, amount=1)
        usr_on_update_sch = UserUpgrateShema(
            username=username if username else None,
            gender=gender if gender else None,
            age=age if age else None,
        )

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            return_value=usr_on_update_orm
        )
        mock_user_repository.update_one = mock.AsyncMock(
            side_effect=[RowAlreadyExists("...")]
        )

        with pytest.raises(UserAlreadyExistsError):
            await user_service.update_one(
                id=usr_on_update_id, updated_user=usr_on_update_sch
            )

            mock_user_repository.get_one_by_id.assert_awaited_once_with(
                id=usr_on_update_id
            )
            mock_user_repository.update_one.assert_awaited_once()

            called_user_orm = mock_user_repository.update_one.call_args.kwargs["user"]
            if usr_on_update_sch.username:
                assert called_user_orm.username == usr_on_update_sch.username
            if usr_on_update_sch.gender:
                assert called_user_orm.gender == usr_on_update_sch.gender
            if usr_on_update_sch.age:
                assert called_user_orm.age == usr_on_update_sch.age

    @pytest.mark.asyncio
    async def test_delete_one_success(
        self,
        mock_user_repository: mock.AsyncMock,
        mock_user_broker: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        usr_on_delete_id = uuid.uuid4()
        usr_on_delete_orm = expected_users_orm_with(id=usr_on_delete_id)

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            return_value=usr_on_delete_orm
        )
        mock_user_repository.delete_one = mock.AsyncMock()
        mock_user_broker.publish = mock.AsyncMock()

        await user_service.delete_one(id=usr_on_delete_id)

        mock_user_repository.get_one_by_id.assert_awaited_once_with(id=usr_on_delete_id)
        mock_user_repository.delete_one.assert_awaited_once_with(user=usr_on_delete_orm)
        mock_user_broker.publish.assert_awaited_once()

        called_publish_data = mock_user_broker.publish.call_args.kwargs["data"]
        assert (
            uuid.UUID(hex=json.loads(called_publish_data)["user_id"])
            == usr_on_delete_id
        )

    @pytest.mark.asyncio
    async def test_delete_one_unexists(
        self,
        mock_user_repository: mock.AsyncMock,
        user_service: "UserService",
    ):
        usr_on_delete_id = uuid.uuid4()

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            side_effect=[NoSuchRowError("...")]
        )

        with pytest.raises(UserNotFoundError):
            await user_service.delete_one(id=usr_on_delete_id)

            mock_user_repository.get_one_by_id.assert_awaited_once_with(
                id=usr_on_delete_id
            )

    @pytest.mark.asyncio
    async def test_delete_one_broker_unreachable(
        self,
        mock_user_repository: mock.AsyncMock,
        mock_user_broker: mock.AsyncMock,
        expected_users_orm_with: Callable,
        user_service: "UserService",
    ):
        usr_on_delete_id = uuid.uuid4()
        usr_on_delete_orm = expected_users_orm_with(id=usr_on_delete_id)

        mock_user_repository.get_one_by_id = mock.AsyncMock(
            return_value=usr_on_delete_orm
        )
        mock_user_broker.publish = mock.AsyncMock(
            side_effect=[UnableToConnectToBrokerError("...")]
        )

        with pytest.raises(UnableToConnectToBrokerError):
            await user_service.delete_one(id=usr_on_delete_id)

            mock_user_repository.get_one_by_id.assert_awaited_once_with(id=usr_on_delete_id)
            mock_user_broker.publish.assert_awaited_once()

            called_publish_data = mock_user_broker.publish.call_args.kwargs["data"]
            assert (
                uuid.UUID(hex=json.loads(called_publish_data)["user_id"])
                == usr_on_delete_id
            )
