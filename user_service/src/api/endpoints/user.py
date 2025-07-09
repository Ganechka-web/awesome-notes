from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from container import Container
from exceptions.broker import UnableToConnectToBrokerError
from exceptions.services import UserNotFoundError, UserAlreadyExistsError
from services.user import UserService
from shemas.user import UserOutputShema, UserUpgrateShema


users_router = APIRouter(prefix="/users")


@users_router.get("/")
@inject
async def get_all(
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> list[UserOutputShema]:
    users = await user_service.get_all()

    return users


@users_router.get("/by-id/{user_id}")
@inject
async def get_one_by_id(
    user_id: Annotated[UUID, Path()],
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> UserOutputShema:
    try:
        user = await user_service.get_one_by_id(id=user_id)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@users_router.get("/by-username/{username}")
@inject
async def get_one_by_username(
    username: Annotated[str, Path()],
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> UserOutputShema:
    try:
        user = await user_service.get_one_by_username(username=username)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@users_router.patch("/update/{user_id}")
@inject
async def update_one(
    user_id: Annotated[UUID, Path()],
    updated_user: UserUpgrateShema,
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        await user_service.update_one(user_id=user_id, updated_user=updated_user)
    except UserAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User with this username - already exists"
        )
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


@users_router.delete("/delete/{user_id}")
@inject
async def delete_one(
    user_id: Annotated[UUID, Path()],
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        await user_service.delete_one(user_id=user_id)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    except UnableToConnectToBrokerError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete user, please try again later",
        )
