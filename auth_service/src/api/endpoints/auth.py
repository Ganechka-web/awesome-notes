from fastapi import APIRouter, HTTPException, Response, status

from core.database import async_engine
from repositories.auth import AuthRepository
from services.auth import AuthService
from schemas.auth import AuthCredentialsRegisterSchema, AuthCredentialsLoginSchema
from exceptions.services import (
    AuthCredentialsAlreadyExistsError,
    AuthCredentialsNotFoundError,
    PasswordsDidNotMatch
)
from exceptions.broker import (
    PublisherCantConnectToBrokerError,
    PublisherTimeoutReceivingResponseError
)


auth_router = APIRouter(prefix='/auth')
auth_repository = AuthRepository(async_engine)
auth_service = AuthService(auth_repository)


@auth_router.post('/register/')
async def register(credentials: AuthCredentialsRegisterSchema) -> str:
    try:
        new_credentials_id = await auth_service.register(
            credentials=credentials
        )
        return new_credentials_id
    except AuthCredentialsAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail='This login already exists'
        )
    except (PublisherCantConnectToBrokerError,
            PublisherTimeoutReceivingResponseError):
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Unable to register, please try again later'
        )


@auth_router.post('/login/')
async def login(
    response: Response, 
    credentials: AuthCredentialsLoginSchema
) -> str:
    try:
        access_token = await auth_service.login(credentials=credentials)
    except AuthCredentialsNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='This login does not exist'
        )
    except PasswordsDidNotMatch:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Password did not match'
        )    
    response.set_cookie('access_token', access_token)

    return access_token
