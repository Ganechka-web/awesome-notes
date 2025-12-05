import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Depends, HTTPException, status
from dependency_injector.wiring import Provide, inject

from src.container import Container
from src.exceptions.broker import UnableToConnectToBrokerError
from src.exceptions.services import UserNotFoundError, UserAlreadyExistsError
from src.services.user import UserService
from src.shemas.user import UserOutputShema, UserUpgrateShema, UserCreateShema


users_router = APIRouter()


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
    user_id: Annotated[uuid.UUID, Path()],
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


@users_router.post("/create/", status_code=status.HTTP_201_CREATED)
@inject
async def create_one(
    new_user: UserCreateShema,
    user_service: UserService = Depends(Provide[Container.user_service]),
) -> uuid.UUID:
    try:
        new_user_id = await user_service.create_one(new_user=new_user)
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username - {new_user.username} already exists",
        )

    return new_user_id


@users_router.patch("/update/{user_id}")
@inject
async def update_one(
    user_id: Annotated[uuid.UUID, Path()],
    updated_user: UserUpgrateShema,
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        await user_service.update_one(id=user_id, updated_user=updated_user)
    except UserAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="User with this username - already exists"
        )
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")


@users_router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_one(
    user_id: Annotated[uuid.UUID, Path()],
    user_service: UserService = Depends(Provide[Container.user_service]),
):
    try:
        await user_service.delete_one(id=user_id)
    except UserNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    except UnableToConnectToBrokerError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to delete user, please try again later",
        )
