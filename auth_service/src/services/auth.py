import json
from uuid import UUID
from typing import TYPE_CHECKING

from schemas.auth import (
    AuthCredentialsSchema,
    AuthCredentialsRegisterSchema,
    AuthCredentialsLoginSchema,
)
from models.auth import AuthCredentials
from exceptions.repositories import RowDoesNotExist
from exceptions.services import (
    AuthCredentialsNotFoundError,
    AuthCredentialsAlreadyExistsError,
    PasswordsDidNotMatch,
    UnableToCreareAuthCredentials,
)
from exceptions.broker import (
    UnableToConnectToBrokerError,
    ReceivingResponseTimeOutError,
)
from security.passwords import get_password_hash, check_password_hash
from security.jwt import get_jwt_token

if TYPE_CHECKING:
    from repositories.auth import AuthRepository
    from broker.rpc_clients import RPCClient


class AuthService:
    def __init__(
        self,
        repository: "AuthRepository",
        rpc_client: "RPCClient",
        user_creation_queue_name: str,
    ) -> None:
        self.repository = repository
        self.rpc_client = rpc_client
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
                common_id = UUID(hex=json.loads(response)["created_user_id"])
            except (
                UnableToConnectToBrokerError,
                ReceivingResponseTimeOutError,
            ) as e:
                raise UnableToCreareAuthCredentials(
                    "Unable to create AuthCredentials, error on the broker side"
                ) from e

            # creating and setting up password hash
            password_hash = get_password_hash(credentials.password)
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
        is_passwords_equal = check_password_hash(
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
