import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from unittest import mock
from contextlib import nullcontext as does_not_raise

import pytest

from src.models.auth import AuthCredentials 
from src.schemas.auth import (
    AuthCredentialsRegisterSchema,
    AuthCredentialsLoginSchema,
    UserEventSchema,
)
from src.schemas.integration_errors import UserServiceCreationErrorSchema
from src.exceptions.services import (
    AuthCredentialsNotFoundError,
    AuthCredentialsAlreadyExistsError,
    UnableToCreareAuthCredentials,
    PasswordsDidNotMatch,
)
from src.exceptions.repositories import RowDoesNotExist
from src.exceptions.integration import UserCreationException
from src.exceptions.broker import (
    UnableToConnectToBrokerError,
    ReceivingResponseTimeOutError,
)
from src.security.jwt import verify_jwt_token

if TYPE_CHECKING:
    from src.services.auth import AuthService


class TestAuthService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        (
            "login",
            "bare_password",
            "is_exists",
            "username",
            "gender",
            "age",
            "expected_exception",
        ),
        (
            (
                "register_login_1",
                "some_bare_password_1",
                False,
                "test_name",
                "male",
                23,
                does_not_raise(),
            ),
            (
                "register_login_1",
                "some_bare_password_2",
                True,
                "test_name_1",
                "female",
                18,
                pytest.raises(AuthCredentialsAlreadyExistsError),
            ),
        ),
    )
    async def test_register(
        self,
        login,
        bare_password,
        is_exists,
        username,
        gender,
        age,
        expected_exception,
        mock_auth_repository: mock.AsyncMock,
        mock_password_service: mock.Mock,
        mock_user_creation_rpc_client: mock.AsyncMock,
        auth_service: "AuthService",
    ):
        # preparing creation data
        user_event_data = UserEventSchema(username=username, gender=gender, age=age)
        auth_credentials_create_schema = AuthCredentialsRegisterSchema(
            login=login, password=bare_password, user_data=user_event_data
        )
        input_rpc_client_data = json.dumps(user_event_data.model_dump()).encode()
        output_rpc_data_data_id = uuid.uuid4().hex
        output_rpc_data_data = {
            "created_user_id": output_rpc_data_data_id,
            "error": None,
        }

        mock_auth_repository.exists = mock.AsyncMock(return_value=is_exists)
        mock_auth_repository.create_one = mock.AsyncMock(
            return_value=uuid.UUID(hex=output_rpc_data_data_id)
        )
        # rpc_client mocking
        mock_user_creation_rpc_client.call = mock.AsyncMock(
            return_value=json.dumps(output_rpc_data_data)
        )
        # password service mocking
        mock_password_service.generate_password_hash.return_value = (
            f"hashed_{bare_password}"
        )

        with expected_exception:
            created_auth_credentials_id = await auth_service.register(
                credentials=auth_credentials_create_schema
            )

            assert created_auth_credentials_id.hex == output_rpc_data_data_id
            mock_auth_repository.exists.assert_awaited_once_with(
                login=auth_credentials_create_schema.login
            )
            mock_auth_repository.create_one.assert_awaited_once()

            mock_user_creation_rpc_client.call.assert_awaited_once_with(
                auth_service.user_creation_queue_name, input_rpc_client_data
            )
            mock_password_service.generate_password_hash.assert_called_with(
                bare_password
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        (
            "login",
            "bare_password",
            "username",
            "gender",
            "age",
            "raised_exception",
            "expected_exception",
        ),
        (
            # user_service is unavailable
            (
                "register_login_1",
                "some_bare_password_1",
                "test_name",
                "male",
                23,
                UnableToConnectToBrokerError("Unable to connect to message broker"),
                pytest.raises(UnableToCreareAuthCredentials),
            ),
            # user_service waiting timeout
            (
                "register_login_1",
                "some_bare_password_2",
                "test_name",
                "female",
                18,
                ReceivingResponseTimeOutError("Receiving timeout expired"),
                pytest.raises(UnableToCreareAuthCredentials),
            ),
        ),
    )
    async def test_register_with_rpc_client_error(
        self,
        login,
        bare_password,
        username,
        gender,
        age,
        raised_exception,
        expected_exception,
        mock_auth_repository: mock.Mock,
        mock_user_creation_rpc_client: mock.Mock,
        auth_service: "AuthService",
    ):
        # preparing creation data
        user_event_data = UserEventSchema(username=username, gender=gender, age=age)
        auth_credentials_create_schema = AuthCredentialsRegisterSchema(
            login=login, password=bare_password, user_data=user_event_data
        )
        input_rpc_client_data = json.dumps(user_event_data.model_dump()).encode()

        # repository methods mocking
        mock_auth_repository.exists = mock.AsyncMock(return_value=False)
        # rpc_client mocking
        mock_user_creation_rpc_client.call = mock.AsyncMock(
            side_effect=raised_exception
        )

        with expected_exception:
            _ = await auth_service.register(credentials=auth_credentials_create_schema)

            mock_user_creation_rpc_client.call.assert_awaited_once_with(
                input_rpc_client_data
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("login", "bare_password", "username", "gender", "age", "exception"),
        (
            # validation or creation error on user_service side
            (
                "register_login_1",
                "some_bare_password_2",
                "test_name",
                "female",
                18,
                pytest.raises(UserCreationException),
            ),
        ),
    )
    async def test_register_with_rpc_client_user_creation_error(
        self,
        login,
        bare_password,
        username,
        gender,
        age,
        exception,
        mock_auth_repository: mock.Mock,
        mock_user_creation_rpc_client: mock.Mock,
        auth_service: "AuthService",
    ):
        # preparing creation data
        user_event_data = UserEventSchema(username=username, gender=gender, age=age)
        auth_credentials_create_schema = AuthCredentialsRegisterSchema(
            login=login, password=bare_password, user_data=user_event_data
        )
        input_rpc_client_data = json.dumps(user_event_data.model_dump()).encode()

        # repository methods mocking
        mock_auth_repository.exists = mock.AsyncMock(return_value=False)

        # rpc_client mocking
        user_service_creation_error_schema = UserServiceCreationErrorSchema(
            message=f"User with username - {username} already exists"
        )
        mock_user_creation_rpc_client.call = mock.AsyncMock(
            return_value=json.dumps(
                {
                    "created_user_id": None,
                    "error": user_service_creation_error_schema.model_dump_json(),
                }
            )
        )

        with exception as exc:
            _ = await auth_service.register(credentials=auth_credentials_create_schema)

            mock_user_creation_rpc_client.call.assert_awaited_with(
                input_rpc_client_data
            )
            assert exc.http_status_code == 409
            assert (
                exc.message_from_service == user_service_creation_error_schema.message
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        (
            "login",
            "password",
            "hashed_password",
            "raised_exception",
            "expected_exception",
        ),
        (
            ("test_user_1", "qwertyui1234", "qwertyui1234", None, does_not_raise()),
            (
                "test_user_2",
                "1234",
                "1235",
                None,
                pytest.raises(PasswordsDidNotMatch),
            ),
            (
                "unexisted_user",
                "some_password",
                "some_password_hash",
                RowDoesNotExist("..."),
                pytest.raises(AuthCredentialsNotFoundError),
            ),
        ),
    )
    async def test_login(
        self,
        login,
        password,
        hashed_password,
        raised_exception,
        expected_exception,
        auth_service: "AuthService",
        mock_auth_repository,
        mock_password_service,
    ):
        auth_credentials_login_schema = AuthCredentialsLoginSchema(
            login=login, password=password
        )
        mock_auth_repository.get_one_by_login = mock.AsyncMock(
            side_effect=raised_exception,
            return_value=AuthCredentials(login=login, password=hashed_password)
        )
        mock_password_service.verify_password_hash = mock.Mock(
            return_value=True if password == hashed_password else False
        )
        with expected_exception:
            access_token = await auth_service.login(
                credentials=auth_credentials_login_schema
            )

            assert isinstance(access_token, str)
            mock_auth_repository.get_one_by_login.assert_awaited_once_with(login=login)
            mock_password_service.verify_password_hash.assert_called_once_with(
                password, hashed_password
            )

            access_token_payload = verify_jwt_token(token=access_token)

            assert access_token_payload["sub"] == login
            assert access_token_payload["exp"] > datetime.now().toordinal()
