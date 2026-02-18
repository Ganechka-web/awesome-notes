import json
from uuid import UUID
from datetime import datetime, timedelta, timezone
from abc import ABC
from typing import TYPE_CHECKING, Any

import jwt

from src.schemas.integration_errors import UserServiceCreationErrorSchema
from src.schemas.auth import (
    AuthCredentialsSchema,
    AuthCredentialsRegisterSchema,
    AuthCredentialsLoginSchema,
)
from src.models.auth import AuthCredentials
from src.exceptions.repositories import RowDoesNotExist
from src.exceptions.services import (
    AuthCredentialsNotFoundError,
    AuthCredentialsAlreadyExistsError,
    PasswordsDidNotMatch,
    InvalidTokenError,
    TokenExpiredError,
    UnableToCreareAuthCredentials,
)
from src.exceptions.integration import UserCreationException
from src.exceptions.broker import (
    UnableToConnectToBrokerError,
    ReceivingResponseTimeOutError,
)
from src.core.settings import ALGORITHM, SECRET_KEY
from src.logger import logger

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository, TokenRepository
    from src.broker.rpc_clients import RPCClient
    from src.services.security import SecurityPasswordService


class Service(ABC):
    pass


class AuthService(Service):
    def __init__(
        self,
        repository: "AuthRepository",
        rpc_client: "RPCClient",
        password_service: "SecurityPasswordService",
        token_service: "JWTTokenService",
        user_creation_queue_name: str,
    ) -> None:
        self.repository = repository
        self.rpc_client = rpc_client
        self.password_service = password_service
        self.token_service = token_service
        self.user_creation_queue_name = user_creation_queue_name

    async def get_one_by_login(self, login: str) -> AuthCredentialsSchema:
        try:
            credentials_orm = await self.repository.get_one_by_login(login=login)
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f"AuthCredentials with login - {login} does not exist"
            ) from e

        return AuthCredentialsSchema.model_validate(credentials_orm)

    async def register(self, credentials: AuthCredentialsRegisterSchema) -> UUID:
        # check credentials existence
        if await self.repository.exists(login=credentials.login):
            raise AuthCredentialsAlreadyExistsError(
                f"AuthCredentials with login - {credentials.login} already exists"
            )
        # call the RPC client to get created user id
        try:
            data = json.dumps(credentials.user_data.model_dump()).encode()
            response = await self.rpc_client.call(self.user_creation_queue_name, data)
            encoded_body = json.loads(response)
        except (
            UnableToConnectToBrokerError,
            ReceivingResponseTimeOutError,
        ) as e:
            raise UnableToCreareAuthCredentials(
                "Unable to create AuthCredentials, error on the broker side"
            ) from e

        # check error on the user_service side
        if encoded_body["error"] is not None:
            encoded_body_error = json.loads(encoded_body["error"])
            error_schema = UserServiceCreationErrorSchema(**encoded_body_error)
            raise UserCreationException(
                msg="Unable to create AuthCredentials because of the invalid user_data",
                http_status_code=error_schema.http_status_code,
                msg_from_service=error_schema.message,
            )

        # creating and setting up password hash
        password_hash = self.password_service.generate_password_hash(
            credentials.password
        )
        credentials.password = password_hash

        auth_credentials = AuthCredentials(
            **credentials.model_dump(
                exclude={
                    "user_data",
                }
            )
        )
        # setting up the common id
        auth_credentials.id = UUID(encoded_body["created_user_id"])
        new_credentials_id = await self.repository.create_one(
            credentials=auth_credentials
        )

        return new_credentials_id

    async def login(self, credentials: AuthCredentialsLoginSchema) -> str:
        """Logins user and returns access token"""
        # checking credentials existence
        try:
            credentials_orm = await self.repository.get_one_by_login(
                login=credentials.login
            )
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f"AuthCredentials with login - {credentials.login} does not exist"
            ) from e

        # checking passwords
        is_passwords_equal = self.password_service.verify_password_hash(
            credentials.password, credentials_orm.password
        )
        if is_passwords_equal:
            # creating jwt token
            access_token = await self.token_service.create_token(credentials.login)
            return access_token
        else:
            raise PasswordsDidNotMatch(
                f"Invalid password for login - {credentials.login}"
            )

    async def check_accessability(self, access_token: str) -> str:
        """Checks if user can get access, returns token back if yes"""
        try:
            access_token = await self.token_service.get_or_update_token(
                token=access_token
            )
        except (InvalidTokenError, TokenExpiredError):
            raise

        return access_token


class JWTTokenService(Service):
    algorithm = ALGORITHM
    sign = SECRET_KEY

    def __init__(self, token_repository: "TokenRepository") -> None:
        self.token_repository = token_repository

    def _create_token(self, payload: dict[str, Any]) -> str:
        """Creates signed token with payload"""
        return jwt.encode(payload, self.sign, algorithm=self.algorithm)

    def _get_payload(self, token: str, verify_exp: bool = False) -> dict[str, Any]:
        """Tries to get token`s payload"""
        try:
            return jwt.decode(
                token,
                key=self.sign,
                algorithms=self.algorithm,
                options={"verify_exp": verify_exp},
            )
        except jwt.DecodeError as e:
            raise InvalidTokenError("Unable to decode the token") from e
        except jwt.ExpiredSignatureError as e:
            raise TokenExpiredError("Token is expired") from e

    async def create_token(
        self,
        sub: str,
        access_payload: dict[str, Any] = {},
        refresh_payload: dict[str, Any] = {},
    ) -> str:
        """Creates and returns access token and saves refresh token"""
        current = datetime.now(tz=timezone.utc)
        access_token = self._create_token(
            payload={
                "sub": sub,
                "iat": current,
                "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=10),
                **access_payload,
            }
        )
        refresh_token = self._create_token(
            payload={
                "sub": sub,
                "iat": current,
                "exp": datetime.now(timezone.utc) + timedelta(days=1),
                **refresh_payload,
            }
        )
        ttl = timedelta(days=1)
        await self.token_repository.save_token(sub, refresh_token, ttl)

        logger.info(f"User with login={sub}, log-in successfully")

        return access_token

    async def get_or_update_token(self, token: str) -> str:
        """
        Verifies the validity of access token via exp.
        Returns new access token if refresh exists

        Warning: All token`s ttl timezone is utc
        """
        current = datetime.now(tz=timezone.utc)
        access_payload = self._get_payload(token)
        # access token is valid
        if datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc) > current:
            return token

        # checking refresh token existence
        if await self.token_repository.is_token_exists(access_payload["sub"]):
            refresh_token = await self.token_repository.get_token(access_payload["sub"])
            refresh_payload = self._get_payload(refresh_token)

            # refresh token is valid
            if (
                datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
                > current
            ):
                return self._create_token(
                    payload={
                        "sub": refresh_payload["sub"],
                        "iat": current,
                        "exp": current + timedelta(minutes=10),
                    }
                )

        raise TokenExpiredError("Tokens are expired")
