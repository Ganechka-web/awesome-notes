import uuid
from unittest import mock

import pytest

from src.schemas.auth import AuthCredentialsSchema, AuthCredentialsLoginSchema
from src.exceptions.integration import UserCreationException
from src.exceptions.services import AuthCredentialsNotFoundError, PasswordsDidNotMatch
from src.security.jwt import get_jwt_token, verify_jwt_token


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("login", "status_code", "raised_exception"),
    (
        ("test_user_1", 200, None),
        ("unexisted_user", 404, AuthCredentialsNotFoundError("...")),
    ),
)
async def test_get_one_by_login(
    login, status_code, raised_exception, client, mock_auth_service
):
    credentials = AuthCredentialsSchema(id=uuid.uuid4(), login=login, password="...")
    mock_auth_service.get_one_by_login = mock.AsyncMock(
        side_effect=raised_exception or [credentials]
    )

    response = client.get(f"/auth/{login}")

    mock_auth_service.get_one_by_login.assert_awaited_once_with(login=login)
    assert response.status_code == status_code

    response_json = response.json()
    if raised_exception:
        assert response_json == {
            "detail": f"AuthCredentials with {login=} does not exist"
        }
    else:
        assert response_json["id"] == str(credentials.id)
        assert response_json["login"] == credentials.login
        assert response_json["password"] == credentials.password


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "login",
        "password",
        "username",
        "gender",
        "age",
        "status_code",
        "raised_exception",
    ),
    (
        (
            "api_test_login",
            "some_test_password",
            "api_test_username",
            "male",
            25,
            201,
            None,
        ),
        (
            "api_test_login_1",
            "some_test_password_1",
            "api_test_username_1",
            "female",
            25,
            201,
            None,
        ),
        (
            "api_test_login_1",
            "some_test_password_1",
            "api_test_username_1",
            "unknown",
            25,
            201,
            None,
        ),
        (
            "api_test_too_long_login",
            "some_test_password",
            "api_test_username",
            "male",
            25,
            422,
            None,
        ),
        (
            "api_error_test_login",
            "some_test_password",
            "api_test_tooooooooooo_loooooooooooong_username_____",
            "male",
            25,
            422,
            None,
        ),
        (
            "api__error_test_login_1",
            "some_test_password",
            "api_test_username_1",
            "whoami",
            25,
            422,
            None,
        ),
        (
            "api_error_test_login_1",
            "some_test_password",
            "api_test_username_1",
            "male",
            17,
            422,
            None,
        ),
        (
            "api_error_test_login",
            "some_test_password",
            "existed_api_test_username",
            "male",
            34,
            409,
            UserCreationException(
                msg="Unable to create AuthCredentials because of the invalid user_data",
                http_status_code=409,
                msg_from_service="User with username - existed_api_test_username already exists",
            ),
        ),
    ),
)
async def test_register(
    login,
    password,
    username,
    gender,
    age,
    status_code,
    raised_exception,
    client,
    mock_auth_service,
):
    register_data = {
        "login": login,
        "password": password,
        "user_data": {"username": username, "gender": gender, "age": age},
    }
    created_credentials_id = uuid.uuid4()

    mock_auth_service.register = mock.AsyncMock(
        side_effect=raised_exception or [created_credentials_id]
    )

    response = client.post("auth/register/", json=register_data)

    assert response.status_code == status_code

    if status_code == 201:
        mock_auth_service.register.assert_awaited_once()
        assert response.content.decode().strip('"') == str(created_credentials_id)

        called_credentials = mock_auth_service.register.call_args.kwargs["credentials"]
        assert called_credentials.login == register_data["login"]
        assert called_credentials.password == register_data["password"]
        assert (
            called_credentials.user_data.username
            == register_data["user_data"]["username"]
        )
        assert (
            called_credentials.user_data.gender == register_data["user_data"]["gender"]
        )
        assert called_credentials.user_data.age == register_data["user_data"]["age"]
    elif raised_exception:
        assert response.json() == {"detail": raised_exception.msg_from_service}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("login", "password", "status_code", "raised_exception"),
    (
        ("test_login_1", "test_password", 200, None),
        ("test_login_2", "test_wrong_password", 401, PasswordsDidNotMatch("...")),
        (
            "test_unexisted_login",
            "unexisted_password",
            404,
            AuthCredentialsNotFoundError("..."),
        ),
    ),
)
async def test_login(
    login, password, status_code, raised_exception, client, mock_auth_service
):
    credentials_login_schema = AuthCredentialsLoginSchema(
        login=login, password=password
    )
    acces_token = get_jwt_token(login)

    mock_auth_service.login = mock.AsyncMock(
        side_effect=raised_exception or [acces_token]
    )

    response = client.post("/auth/login/", json=credentials_login_schema.model_dump())

    assert response.status_code == status_code

    mock_auth_service.login.assert_awaited_once()
    call_param_credentials = mock_auth_service.login.call_args.kwargs["credentials"]
    assert call_param_credentials.login == login
    assert call_param_credentials.password == password

    if not raised_exception:
        token_payload = verify_jwt_token(response.json())
        assert token_payload["sub"] == login
    else:
        assert "detail" in response.json()
