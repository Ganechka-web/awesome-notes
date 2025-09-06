import json
from uuid import UUID
from typing import TYPE_CHECKING

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
    UnableToCreareAuthCredentials,
)
from src.exceptions.integration import UserCreationException
from src.exceptions.broker import (
    UnableToConnectToBrokerError,
    ReceivingResponseTimeOutError,
)
from src.security.jwt import get_jwt_token

if TYPE_CHECKING:
    from src.repositories.auth import AuthRepository
    from src.broker.rpc_clients import RPCClient
    from src.services.security import SecurityPasswordService


class AuthService:
    def __init__(
        self,
        repository: "AuthRepository",
        rpc_client: "RPCClient",
        password_service: "SecurityPasswordService",
        user_creation_queue_name: str,
    ) -> None:
        self.repository = repository
        self.rpc_client = rpc_client
        self.password_service = password_service
        self.user_creation_queue_name = user_creation_queue_name

    async def get_one_by_login(self, login: str) -> AuthCredentialsSchema:
        try:
            credentials_orm = await self.repository.get_one_by_login(login=login)
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f"AuthCredentials with login - {login} does not exist"
            ) from e

        return AuthCredentialsSchema.model_validate(credentials_orm)

    async def register(self, credentials: AuthCredentialsRegisterSchema) -> str:
        # check credentials existence
        common_id: UUID = 0  # rewrite
        try:
            _ = await self.repository.get_one_by_login(login=credentials.login)
            raise AuthCredentialsAlreadyExistsError(
                f"AuthCredentials with login - {credentials.login} already exists"
            )
        except RowDoesNotExist:
            # call the RPC client to get created user id
            try:
                data = json.dumps(credentials.user_data.model_dump()).encode()
                response = await self.rpc_client.call(
                    self.user_creation_queue_name, data
                )
                encoded_body = json.loads(response)
                encoded_body_error = json.loads(encoded_body["error"])

            except (
                UnableToConnectToBrokerError,
                ReceivingResponseTimeOutError,
            ) as e:
                raise UnableToCreareAuthCredentials(
                    "Unable to create AuthCredentials, error on the broker side"
                ) from e

            # check error on the user_service side
            if encoded_body_error is not None:
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
                **credentials.model_dump(exclude="user_data")
            )
            # setting up the common id
            auth_credentials.id = common_id
            new_credentials_id = await self.repository.create_one(
                credentials=auth_credentials
            )

            return new_credentials_id

    async def login(self, credentials: AuthCredentialsLoginSchema) -> str:
        # check credentials existence
        try:
            credentials_orm = await self.repository.get_one_by_login(
                login=credentials.login
            )
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f"AuthCredentials with login - {credentials.login} does not exist"
            ) from e

        # check passwords
        is_passwords_equal = self.password_service.verify_password_hash(
            credentials.password, credentials_orm.password
        )
        if is_passwords_equal:
            # generate jwt token
            access_token = get_jwt_token(credentials.login)

            return access_token
        else:
            raise PasswordsDidNotMatch(
                f"Invalid password for login - {credentials.login}"
            )
