import uuid
from typing import Callable
from unittest import mock

import pytest
from fastapi.testclient import TestClient

from src.exceptions.services import UserNotFoundError, UserAlreadyExistsError
from src.exceptions.broker import UnableToConnectToBrokerError


def test_get_all(
    expected_users_sch_with: Callable,
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_users_sch = expected_users_sch_with(amount=15)
    mock_user_service.get_all = mock.AsyncMock(return_value=exp_users_sch)

    response = client.get("user/")

    assert response.status_code == 200
    mock_user_service.get_all.assert_awaited_once()

    for exp_user, res_user in zip(exp_users_sch, response.json()):
        assert exp_user.id == uuid.UUID(res_user["id"])
        assert exp_user.username == res_user["username"]
        assert exp_user.age == res_user["age"]
        assert exp_user.gender == res_user["gender"]
        assert exp_user.joined_at.isoformat() == res_user["joined_at"]
        assert exp_user.updated_at.isoformat() == res_user["updated_at"]


def test_get_all_empty(mock_user_service: mock.AsyncMock, client: TestClient):
    mock_user_service.get_all = mock.AsyncMock(return_value=[])

    response = client.get("/user/")

    assert response.status_code == 200
    mock_user_service.get_all.assert_awaited_once()
    assert response.json() == []


def test_get_one_by_id(
    expected_users_sch_with: Callable,
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_user_id = uuid.uuid4()
    exp_user_sch = expected_users_sch_with(id=exp_user_id)
    mock_user_service.get_one_by_id = mock.AsyncMock(return_value=exp_user_sch)

    response = client.get(f"/user/by-id/{exp_user_id}")

    assert response.status_code == 200
    assert uuid.UUID(response.json()["id"]) == exp_user_id
    mock_user_service.get_one_by_id.assert_awaited_once_with(id=exp_user_id)


def test_get_one_by_id_unexists(
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_user_id = uuid.uuid4()
    mock_user_service.get_one_by_id = mock.AsyncMock(
        side_effect=[UserNotFoundError("...")]
    )

    response = client.get(f"/user/by-id/{exp_user_id}")

    assert response.status_code == 404
    mock_user_service.get_one_by_id.assert_awaited_once_with(id=exp_user_id)


def test_get_one_by_username(
    expected_users_sch_with: Callable,
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_user_username = "Some_username"
    exp_user_sch = expected_users_sch_with(username=exp_user_username)
    mock_user_service.get_one_by_username = mock.AsyncMock(return_value=exp_user_sch)

    response = client.get(f"/user/by-username/{exp_user_username}")

    assert response.status_code == 200
    assert response.json()["username"] == exp_user_username
    mock_user_service.get_one_by_username.assert_awaited_once_with(
        username=exp_user_username
    )


def test_get_one_by_username_unexists(
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_user_username = "Some_username"
    mock_user_service.get_one_by_username = mock.AsyncMock(
        side_effect=[UserNotFoundError("...")]
    )

    response = client.get(f"/user/by-username/{exp_user_username}")

    assert response.status_code == 404
    mock_user_service.get_one_by_username.assert_awaited_once_with(
        username=exp_user_username
    )


@pytest.mark.parametrize(
    ("username", "gender", "age"),
    (
        ("Some_valid_username_1", "male", 38),
        ("Some_valid_username_1", "female", 74),
        ("Some_valid_username_1", "unknown", 22),
    ),
)
def test_create_one_success(
    username: str,
    gender: str,
    age: int,
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    exp_new_user_id = uuid.uuid4()
    create_data = {"username": username, "gender": gender, "age": age}
    mock_user_service.create_one = mock.AsyncMock(return_value=exp_new_user_id)

    response = client.post("/user/create/", json=create_data)

    assert response.status_code == 201
    assert uuid.UUID(response.json()) == exp_new_user_id
    mock_user_service.create_one.assert_awaited_once()

    called_user_sch = mock_user_service.create_one.call_args.kwargs["new_user"]
    assert called_user_sch.username == username
    assert called_user_sch.gender == gender
    assert called_user_sch.age == age


@pytest.mark.parametrize(
    ("username", "gender", "age"),
    (
        ("Some_valid_username_1", "somebody", 38),  # incorrect gender
        ("Some_valid_username_1", "female", 0),  # too young age
        ("Some_valid_username_1", "female", 111),  # too old age
        (
            "Some_valid_username_1_too_long_too_long_too_long_too_long_too_long",
            "unknown",
            22,
        ),  # too long username
    ),
)
def test_create_one_validation_failed(
    username: str,
    gender: str,
    age: int,
    client: TestClient,
):
    create_data = {"username": username, "gender": gender, "age": age}

    response = client.post("/user/create/", json=create_data)

    assert response.status_code == 422


def test_create_one_already_exists(
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    create_data = {"username": "Already_existed_username", "gender": "male", "age": 18}
    mock_user_service.create_one = mock.AsyncMock(
        side_effect=[UserAlreadyExistsError("...")]
    )

    response = client.post("/user/create/", json=create_data)

    assert response.status_code == 409
    mock_user_service.create_one.assert_awaited_once()

    called_user_sch = mock_user_service.create_one.call_args.kwargs["new_user"]
    assert called_user_sch.username == create_data["username"]
    assert called_user_sch.gender == create_data["gender"]
    assert called_user_sch.age == create_data["age"]


@pytest.mark.parametrize(
    ("username", "gender", "age"),
    (
        ("Some_valid_username_1", "male", 38),
        ("Some_valid_username_1", None, None),
        (None, "unknown", None),
        (None, None, 22),
    ),
)
def test_update_one(
    username: str,
    gender: str,
    age: int,
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    update_data = {"username": username, "gender": gender, "age": age}
    updated_user_id = uuid.uuid4()
    mock_user_service.update_one = mock.AsyncMock()

    response = client.patch(f"/user/update/{updated_user_id}", json=update_data)

    assert response.status_code == 200
    mock_user_service.update_one.assert_awaited_once()

    called_user_sch = mock_user_service.update_one.call_args.kwargs["updated_user"]
    assert called_user_sch.username == update_data["username"]
    assert called_user_sch.gender == update_data["gender"]
    assert called_user_sch.age == update_data["age"]


@pytest.mark.parametrize(
    ("username", "gender", "age"),
    (
        ("Some_valid_username_1", "somebody", 38),  # incorrect gender
        ("Some_valid_username_1", "female", 0),  # too young age
        ("Some_valid_username_1", "female", 111),  # too old age
        (
            "Some_valid_username_1_too_long_too_long_too_long_too_long_too_long",
            "unknown",
            22,
        ),  # too long username
    ),
)
def test_update_one_validation_failed(
    username: str, gender: str, age: int, client: TestClient
):
    update_data = {"username": username, "gender": gender, "age": age}
    updated_user_id = uuid.uuid4()

    response = client.patch(f"/user/update/{updated_user_id}", json=update_data)

    assert response.status_code == 422


def test_update_one_already_exists(
    mock_user_service: mock.AsyncMock,
    client: TestClient,
):
    update_data = {"username": "Already_existed_username"}
    updated_user_id = uuid.uuid4()
    mock_user_service.update_one = mock.AsyncMock(
        side_effect=UserAlreadyExistsError("...")
    )

    response = client.patch(f"/user/update/{updated_user_id}", json=update_data)

    assert response.status_code == 409
    mock_user_service.update_one.assert_awaited_once()

    called_user_sch = mock_user_service.update_one.call_args.kwargs["updated_user"]
    assert called_user_sch.username == update_data["username"]


def test_delete_one_success(mock_user_service: mock.AsyncMock, client: TestClient):
    user_on_delete_id = uuid.uuid4()
    mock_user_service.delete_one = mock.AsyncMock()

    response = client.delete(f"/user/delete/{user_on_delete_id}")

    assert response.status_code == 204
    mock_user_service.delete_one.assert_awaited_once_with(id=user_on_delete_id)


def test_delete_one_broker_unreachable(
    mock_user_service: mock.AsyncMock, client: TestClient
):
    user_on_delete_id = uuid.uuid4()
    mock_user_service.delete_one = mock.AsyncMock(
        side_effect=[UnableToConnectToBrokerError("...")]
    )

    response = client.delete(f"/user/delete/{user_on_delete_id}")

    assert response.status_code == 503
    mock_user_service.delete_one.assert_awaited_once_with(id=user_on_delete_id)


def test_delete_one_unexists(mock_user_service: mock.AsyncMock, client: TestClient):
    user_on_delete_id = uuid.uuid4()
    mock_user_service.delete_one = mock.AsyncMock(
        side_effect=[UserNotFoundError("...")]
    )

    response = client.delete(f"/user/delete/{user_on_delete_id}")

    assert response.status_code == 404
    mock_user_service.delete_one.assert_awaited_once_with(id=user_on_delete_id)
