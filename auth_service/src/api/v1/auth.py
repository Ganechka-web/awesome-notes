from uuid import UUID
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, HTTPException, Response, Depends, Path, status
from dependency_injector.wiring import Provide, inject

from src.schemas.auth import (
    AuthCredentialsRegisterSchema,
    AuthCredentialsLoginSchema,
    AuthCredentialsSchema,
)
from src.exceptions.integration import UserCreationException
from src.exceptions.services import (
    AuthCredentialsAlreadyExistsError,
    AuthCredentialsNotFoundError,
    PasswordsDidNotMatch,
    UnableToCreareAuthCredentials,
)
from src.container import Container
from src.logger import logger

if TYPE_CHECKING:
    from src.services.auth import AuthService


auth_router = APIRouter()


@auth_router.get("/{login}")
@inject
async def get_one_by_login(
    login: Annotated[str, Path()],
    auth_service: "AuthService" = Depends(Provide[Container.auth_service]),
) -> AuthCredentialsSchema:
    try:
        credentials = await auth_service.get_one_by_login(login=login)
    except AuthCredentialsNotFoundError:
        return HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"AuthCredentials with {login=} does not exist"
        )

    return credentials

@auth_router.post("/register/")
@inject
async def register(
    credentials: AuthCredentialsRegisterSchema,
    auth_service: "AuthService" = Depends(Provide[Container.auth_service]),
) -> UUID:
    try:
        new_credentials_id = await auth_service.register(credentials=credentials)
    except AuthCredentialsAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="This login already exists"
        )
    except UnableToCreareAuthCredentials as e:
        logger.error(f"User hasn`t been created, info: {e.msg}")
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to register, please try again later",
        )
    except UserCreationException as e:
        logger.error(
            f"User hasn`t been created because of user_service error, "
            f"status code - {e.http_status_code} info - {e.msg_from_service}"
        )
        raise HTTPException(e.http_status_code, detail=e.msg_from_service)

    return new_credentials_id


@auth_router.post("/login/")
@inject
async def login(
    response: Response,
    credentials: AuthCredentialsLoginSchema,
    auth_service: "AuthService" = Depends(Provide[Container.auth_service]),
) -> str:
    try:
        access_token = await auth_service.login(credentials=credentials)
    except AuthCredentialsNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail="This login does not exist"
        )
    except PasswordsDidNotMatch:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, detail="Password did not match"
        )
    response.set_cookie("access_token", access_token)

    return access_token
