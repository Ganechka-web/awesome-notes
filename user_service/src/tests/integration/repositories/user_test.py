import uuid
from typing import TYPE_CHECKING, Callable
from datetime import datetime

import pytest

from src.exceptions.repositories import NoSuchRowError, RowAlreadyExists
from src.models.user import Gender

if TYPE_CHECKING:
    from src.repositories.user import UserRepository


class TestUserRepository:
    @pytest.mark.asyncio
    async def test_get_all(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        expected_users_amount = 10
        expected_users_orm, expected_users_attrs = expected_users_and_attrs_orm_with(
            amount=expected_users_amount
        )
        await insert_test_data(expected_users_orm)

        users = await user_repository.get_all()

        assert len(users) == expected_users_amount
        for usr_orm, exp_usr_orm in zip(users, expected_users_attrs):
            assert usr_orm.id == exp_usr_orm["id"]
            assert usr_orm.username == exp_usr_orm["username"]
            assert usr_orm.gender.value == exp_usr_orm["gender"]
            assert usr_orm.age == exp_usr_orm["age"]
            assert isinstance(usr_orm.joined_at, datetime)
            assert isinstance(usr_orm.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_get_one_by_id(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        expected_user_id = uuid.uuid4()
        expected_user_orm, expected_user_attrs = expected_users_and_attrs_orm_with(
            id=expected_user_id, amount=1
        )
        await insert_test_data([expected_user_orm])

        user = await user_repository.get_one_by_id(id=expected_user_id)

        assert user.id == expected_user_id
        assert user.username == expected_user_attrs["username"]
        assert user.gender.value == expected_user_attrs["gender"]
        assert user.age == expected_user_attrs["age"]
        assert isinstance(user.joined_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_get_one_by_id_unexists(self, user_repository: "UserRepository"):
        expected_user_id = uuid.uuid4()

        with pytest.raises(NoSuchRowError):
            _ = await user_repository.get_one_by_id(id=expected_user_id)

    @pytest.mark.asyncio
    async def test_get_one_by_username(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        expected_user_username = "Some_username"
        expected_user_orm, expected_user_attrs = expected_users_and_attrs_orm_with(
            username=expected_user_username, amount=1
        )
        await insert_test_data([expected_user_orm])

        user = await user_repository.get_one_by_username(
            username=expected_user_username
        )

        assert user.id == expected_user_attrs["id"]
        assert user.username == expected_user_username
        assert user.gender.value == expected_user_attrs["gender"]
        assert user.age == expected_user_attrs["age"]
        assert isinstance(user.joined_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_get_one_by_username_unexists(
        self, user_repository: "UserRepository"
    ):
        expected_user_username = "Some_unexists_username"

        with pytest.raises(NoSuchRowError):
            _ = await user_repository.get_one_by_username(
                username=expected_user_username
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("id", "username", "expected"),
        (
            (uuid.uuid4(), "Existed_username", True),
            (uuid.uuid4(), None, True),
            (None, "Existed_username", True),
        ),
    )
    async def test_exists(
        self,
        id,
        username,
        expected,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        expected_user_orm, _ = expected_users_and_attrs_orm_with(
            id=id, username=username, amount=1
        )
        await insert_test_data([expected_user_orm])

        result = await user_repository.exists(id=id, username=username)

        assert result == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("id", "username", "expected"),
        (
            (uuid.uuid4(), "Existed_username", False),
            (uuid.uuid4(), None, False),
            (None, "Existed_username", False),
            (None, None, False),
        ),
    )
    async def test_exists_unexists(
        self,
        id,
        username,
        expected,
        user_repository: "UserRepository",
    ):
        result = await user_repository.exists(id=id, username=username)

        assert result == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("username", "gender", "age"),
        (
            ("Some_username", "male", 65),
            ("Some_username_1", "female", 22),
            ("Some_username_2", "unknown", 33),
            ("Some_username_2", "unknown", 110),
            ("Some_username_2", "unknown", 18),
            ("Some_username_2_too_largelargelargelargelargelarge", "unknown", 57),
        ),
    )
    async def test_create_one(
        self,
        username,
        gender,
        age,
        expected_users_and_attrs_orm_with: Callable,
        user_repository: "UserRepository",
    ):
        user_on_create_orm, user_on_create_attrs = expected_users_and_attrs_orm_with(
            username=username, gender=gender, age=age, amount=1
        )

        created_user_id = await user_repository.create_one(user=user_on_create_orm)

        created_user = await user_repository.get_one_by_id(id=created_user_id)
        assert created_user.username == user_on_create_attrs["username"]
        assert created_user.gender.value == user_on_create_attrs["gender"]
        assert created_user.age == user_on_create_attrs["age"]
        assert isinstance(created_user.joined_at, datetime)
        assert isinstance(created_user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_one_already_exists(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        user_on_create_username = "Some_existed_username"
        user_on_create_orm, _ = expected_users_and_attrs_orm_with(
            username=user_on_create_username, amount=1
        )
        await insert_test_data([user_on_create_orm])

        already_existed_user, _ = expected_users_and_attrs_orm_with(
            username=user_on_create_username, amount=1
        )

        with pytest.raises(RowAlreadyExists):
            _ = await user_repository.create_one(user=already_existed_user)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("username", "gender", "age"),
        (
            ("Some_username", Gender.male, 65),
            ("Some_username_1", Gender.female, 22),
            ("Some_username_2", Gender.unknown, 33),
            ("Some_username_2", Gender.unknown, 110),
            ("Some_username_2", Gender.unknown, 18),
            ("Some_username_2_too_largelargelargelargelargelarge", Gender.unknown, 57),
            ("Some_username_only", None, None),
            (None, Gender.male, None),
            (None, None, 38),
        ),
    )
    async def test_update_one(
        self,
        username,
        gender,
        age,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        created_user_id = uuid.uuid4()
        user_on_create_orm, user_on_create_attrs = expected_users_and_attrs_orm_with(
            id=created_user_id, amount=1
        )
        await insert_test_data([user_on_create_orm])

        user_on_update = await user_repository.get_one_by_id(id=created_user_id)
        orig_updated_at = user_on_update.updated_at
        if username:
            user_on_update.username = username
        if gender:
            user_on_update.gender = gender
        if age:
            user_on_update.age = age

        await user_repository.update_one(user=user_on_update)

        updated_user = await user_repository.get_one_by_id(id=created_user_id)
        assert updated_user.username == username or user_on_create_attrs["username"]
        assert updated_user.gender == gender or user_on_create_attrs["gender"]
        assert updated_user.age == age or user_on_create_attrs["age"]
        assert isinstance(updated_user.joined_at, datetime)
        assert updated_user.updated_at > orig_updated_at

    @pytest.mark.asyncio
    async def test_update_one_already_exists(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        created_user_id = uuid.uuid4()
        user_on_create_username = "Some_existed_username"
        user_on_create_orm, _ = expected_users_and_attrs_orm_with(
            id=created_user_id, username=user_on_create_username, amount=1
        )
        await insert_test_data([user_on_create_orm])

        user_on_update_existed, _ = expected_users_and_attrs_orm_with(
            username=user_on_create_username, amount=1
        )

        with pytest.raises(RowAlreadyExists):
            await user_repository.update_one(user=user_on_update_existed)

    @pytest.mark.asyncio
    async def test_delete_one(
        self,
        expected_users_and_attrs_orm_with: Callable,
        insert_test_data: Callable,
        user_repository: "UserRepository",
    ):
        created_user_id = uuid.uuid4()
        user_on_create_orm, _ = expected_users_and_attrs_orm_with(
            id=created_user_id, amount=1
        )
        await insert_test_data([user_on_create_orm])

        created_user = await user_repository.get_one_by_id(id=created_user_id)

        await user_repository.delete_one(user=created_user)

        with pytest.raises(NoSuchRowError):
            await user_repository.get_one_by_id(id=created_user_id)
