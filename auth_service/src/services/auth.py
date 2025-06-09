from schemas.auth import (
    AuthCredentialsSchema,
    AuthCredentialsRegisterSchema,
    AuthCredentialsLoginSchema
)
from models.auth import AuthCredentials
from repositories.auth import AuthRepository
from exceptions.repositories import RowDoesNotExist, RowAlreadyExists
from exceptions.services import (
    AuthCredentialsNotFoundError, 
    AuthCredentialsAlreadyExistsError,
    PasswordsDidNotMatch
)
from security.passwords import get_password_hash, check_password_hash
from security.jwt import get_jwt_token


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def get_one_by_login(self, login: str) -> AuthCredentialsSchema:
        try:
            credentials_orm = await self.repository.get_one_by_login(
                login=login
            )
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f'AuthCredentials with login - {login}'
                'does not exist'
            ) from e

        return AuthCredentialsSchema.model_validate(credentials_orm)
    
    async def register(self, credentials: AuthCredentialsRegisterSchema) -> int:
        password_hash = get_password_hash(credentials.password)
        credentials.password = password_hash

        auth_credentials = AuthCredentials(**credentials.model_dump())
        try:
            new_credentials_id = await self.repository.create_one(
                credentials=auth_credentials
            )
        except RowAlreadyExists as e:
            raise AuthCredentialsAlreadyExistsError(
                f'AuthCredentials with login - {credentials.login}'
                'already exist'
            ) from e
        
        return new_credentials_id
    
    async def login(self, credentials: AuthCredentialsLoginSchema) -> str:
        # check credentials existence
        try:
            credentials_orm = await self.repository.get_one_by_login(
                login=credentials.login
            )
        except RowDoesNotExist as e:
            raise AuthCredentialsNotFoundError(
                f'AuthCredentials with login - {credentials.login}'
                'does not exist'
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
                f'Invalid password for login - {credentials.login}'
            )
