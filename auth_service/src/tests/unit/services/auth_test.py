import json
import uuid
from unittest import mock
from datetime import timedelta, datetime, timezone
from typing import TYPE_CHECKING, Callable
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
    InvalidTokenError,
    TokenExpiredError,
)
from src.exceptions.repositories import RowDoesNotExist
from src.exceptions.integration import UserCreationException
from src.exceptions.broker import (
    UnableToConnectToBrokerError,
    ReceivingResponseTimeOutError,
)

if TYPE_CHECKING:
    from src.services.auth import AuthService, JWTTokenService


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
        login: str,
        bare_password: str,
        username: str,
        gender: str,
        age: int,
        exception: pytest.RaisesExc,
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
        login: str,
        password: str,
        hashed_password: str,
        raised_exception: Exception,
        expected_exception: pytest.RaisesExc,
        mock_auth_repository: mock.AsyncMock,
        mock_token_service: mock.AsyncMock,
        mock_password_service: mock.Mock,
        auth_service: "AuthService",
    ):
        auth_credentials_login_schema = AuthCredentialsLoginSchema(
            login=login, password=password
        )
        mock_auth_repository.get_one_by_login = mock.AsyncMock(
            side_effect=raised_exception,
            return_value=AuthCredentials(login=login, password=hashed_password),
        )
        mock_password_service.verify_password_hash = mock.Mock(
            return_value=True if password == hashed_password else False
        )
        returned_access_token = "ewfjnvbowenvnoewuvih48932vo4208v8"
        mock_token_service.create_token = mock.AsyncMock(
            return_value=returned_access_token
        )

        with expected_exception:
            access_token = await auth_service.login(
                credentials=auth_credentials_login_schema
            )

            assert access_token == returned_access_token
            mock_auth_repository.get_one_by_login.assert_awaited_once_with(login=login)
            mock_password_service.verify_password_hash.assert_called_once_with(
                password, hashed_password
            )
            mock_token_service.create_token.assert_awaited_once_with(login)

    @pytest.mark.asyncio
    async def test_check_accessability_valid_token(
        self, mock_token_service: mock.AsyncMock, auth_service: "AuthService"
    ):
        token = "ewfjnvbowenvnoewuvih48932vo4208v8"
        mock_token_service.get_or_update_token = mock.AsyncMock(return_value=token)

        returned_token = await auth_service.check_accessability(access_token=token)

        assert returned_token == token

    @pytest.mark.asyncio
    async def test_check_accessability_invalid_token(
        self, mock_token_service: mock.AsyncMock, auth_service: "AuthService"
    ):
        token = "ewfjnvbowenvnoewuvih48932vo4208v8"
        mock_token_service.get_or_update_token = mock.AsyncMock(
            side_effect=InvalidTokenError("...")
        )

        with pytest.raises(InvalidTokenError):
            _ = await auth_service.check_accessability(access_token=token)

    @pytest.mark.asyncio
    async def test_check_accessability_expired_token(
        self, mock_token_service: mock.AsyncMock, auth_service: "AuthService"
    ):
        token = "ewfjnvbowenvnoewuvih48932vo4208v8"
        mock_token_service.get_or_update_token = mock.AsyncMock(
            side_effect=TokenExpiredError("...")
        )

        with pytest.raises(TokenExpiredError):
            _ = await auth_service.check_accessability(access_token=token)


class TestJWTTokenService:
    @pytest.mark.asyncio
    async def test_create_token(
        self,
        mock_redis_token_repository: mock.AsyncMock,
        decode_jwt_token: Callable,
        jwt_token_service: "JWTTokenService",
    ):
        sub = "some_username"
        access_token_life_time = timedelta(minutes=10)
        refresh_token_life_time = timedelta(days=1)
        additional_access_token_payload = {"access_key": "value"}
        additional_refresh_token_payload = {"refresh_key": "value"}
        mock_redis_token_repository.save_token = mock.AsyncMock()

        access_token = await jwt_token_service.create_token(
            sub=sub,
            access_payload=additional_access_token_payload,
            refresh_payload=additional_refresh_token_payload,
        )

        access_payload = decode_jwt_token(token=access_token)
        assert access_payload["sub"] == sub
        assert (
            access_payload["exp"] - access_payload["iat"]
            == access_token_life_time.total_seconds()
        )

        mock_redis_token_repository.save_token.assert_awaited_once()
        refresh_payload = decode_jwt_token(
            token=mock_redis_token_repository.save_token.call_args.args[1]
        )
        assert refresh_payload["sub"] == sub
        assert (
            refresh_payload["exp"] - refresh_payload["iat"]
            == refresh_token_life_time.total_seconds()
        )

    @pytest.mark.asyncio
    async def test_get_or_update_token_valid_access(
        self,
        encode_jwt_token: Callable,
        jwt_token_service: "JWTTokenService",
    ):
        sub = "some_user_username_gout"
        current_datetime = datetime.now(tz=timezone.utc)
        access_payload = {
            "sub": sub,
            "iat": current_datetime,
            "exp": current_datetime + timedelta(minutes=8),
        }
        old_access_token = encode_jwt_token(payload=access_payload)

        access_token = await jwt_token_service.get_or_update_token(
            token=old_access_token
        )

        assert access_token == old_access_token

    @pytest.mark.asyncio
    async def test_get_or_update_token_invalid_access(
        self,
        mock_redis_token_repository: mock.AsyncMock,
        encode_jwt_token: Callable,
        decode_jwt_token: Callable,
        jwt_token_service: "JWTTokenService",
    ):
        sub = "some_user_username_gout"
        current_datetime = datetime.now(tz=timezone.utc)
        old_access_payload = {
            "sub": sub,
            "iat": current_datetime - timedelta(minutes=10),
            "exp": current_datetime,
        }
        old_access_token = encode_jwt_token(payload=old_access_payload)

        refresh_payload = {
            "sub": sub,
            "iat": current_datetime - timedelta(minutes=10),
            "exp": current_datetime + timedelta(days=1),
        }
        refresh_token = encode_jwt_token(payload=refresh_payload)
        mock_redis_token_repository.is_token_exists = mock.AsyncMock(return_value=True)
        mock_redis_token_repository.get_token = mock.AsyncMock(
            return_value=refresh_token
        )

        access_token = await jwt_token_service.get_or_update_token(
            token=old_access_token
        )

        assert access_token != old_access_token

        access_payload = decode_jwt_token(token=access_token)
        assert access_payload["sub"] == sub
        assert (
            access_payload["exp"] - access_payload["iat"]
            == timedelta(minutes=10).seconds
        )

        mock_redis_token_repository.is_token_exists.assert_awaited_once_with(sub)
        mock_redis_token_repository.get_token.assert_awaited_once_with(sub)

    @pytest.mark.asyncio
    async def test_get_or_update_token_elapsed_access_and_refresh(
        self,
        mock_redis_token_repository: mock.AsyncMock,
        encode_jwt_token: Callable,
        jwt_token_service: "JWTTokenService",
    ):
        sub = "some_user_username_gout"
        current_datetime = datetime.now(tz=timezone.utc)
        old_access_payload = {
            "sub": sub,
            "iat": current_datetime - timedelta(days=1),
            "exp": current_datetime,
        }
        old_access_token = encode_jwt_token(payload=old_access_payload)

        refresh_payload = {
            "sub": sub,
            "iat": current_datetime - timedelta(days=1),
            "exp": current_datetime,
        }
        refresh_token = encode_jwt_token(payload=refresh_payload)
        mock_redis_token_repository.is_token_exists = mock.AsyncMock(return_value=True)
        mock_redis_token_repository.get_token = mock.AsyncMock(
            return_value=refresh_token
        )

        with pytest.raises(TokenExpiredError):
            _ = await jwt_token_service.get_or_update_token(token=old_access_token)

            mock_redis_token_repository.is_token_exists.assert_awaited_once_with(sub)
            mock_redis_token_repository.get_token.assert_awaited_once_with(sub)

    @pytest.mark.asyncio
    async def test_get_or_update_token_elapsed_access_refresh_unexists(
        self,
        mock_redis_token_repository: mock.AsyncMock,
        encode_jwt_token: Callable,
        jwt_token_service: "JWTTokenService",
    ):
        sub = "some_user_username_gout"
        current_datetime = datetime.now(tz=timezone.utc)
        old_access_payload = {
            "sub": sub,
            "iat": current_datetime - timedelta(days=1),
            "exp": current_datetime,
        }
        old_access_token = encode_jwt_token(payload=old_access_payload)

        mock_redis_token_repository.is_token_exists = mock.AsyncMock(return_value=False)

        with pytest.raises(TokenExpiredError):
            _ = await jwt_token_service.get_or_update_token(token=old_access_token)

            mock_redis_token_repository.is_token_exists.assert_awaited_once_with(sub)
