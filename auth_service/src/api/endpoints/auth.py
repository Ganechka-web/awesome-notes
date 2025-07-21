from uuid import UUID
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Response, Depends, status
from dependency_injector.wiring import Provide, inject

from schemas.auth import AuthCredentialsRegisterSchema, AuthCredentialsLoginSchema
from exceptions.services import (
    AuthCredentialsAlreadyExistsError,
    AuthCredentialsNotFoundError,
    PasswordsDidNotMatch,
    UnableToCreareAuthCredentials,
)
from container import Container

if TYPE_CHECKING:
    from services.auth import AuthService


auth_router = APIRouter(prefix="/auth")


@auth_router.post("/register/")
@inject
async def register(
    credentials: AuthCredentialsRegisterSchema,
    auth_service: "AuthService" = Depends(Provide[Container.auth_service]),
) -> UUID:
    try:
        new_credentials_id = await auth_service.register(credentials=credentials)
        return new_credentials_id
    except AuthCredentialsAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="This login already exists"
        )
    except UnableToCreareAuthCredentials:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to register, please try again later",
        )


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
