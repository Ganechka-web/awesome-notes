from typing import Annotated

from fastapi import (
    APIRouter, Path, 
    HTTPException, status
)

from core.database import async_engine
from repositories.user import UserRepository
from services.user import UserService
from exceptions.services import (
    UserNotFoundError,
    UserAlreadyExistsError
)
from exceptions.broker import PublisherCantConnectToBrokerError
from shemas.user import (
    UserOutputShema, 
    UserUpgrateShema
)


users_router = APIRouter(prefix='/users')

user_repository = UserRepository(async_engine)
user_service = UserService(user_repository)


@users_router.get('/')
async def get_all() -> list[UserOutputShema]:
    users = await user_service.get_all()

    return users


@users_router.get('/by-id/{user_id}')
async def get_one_by_id(user_id: Annotated[int, Path()]) -> UserOutputShema:
    try:
        user = await user_service.get_one_by_id(id=user_id)
    except UserNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

    return user


@users_router.get('/by-username/{username}')
async def get_one_by_username(username: Annotated[str, Path()]) -> UserOutputShema:
    try:
        user = await user_service.get_one_by_username(username=username)
    except UserNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )

    return user


@users_router.patch('/update/{user_id}')
async def update_one(user_id: Annotated[int, Path()], 
                     updated_user: UserUpgrateShema):
    try:
        await user_service.update_one(user_id=user_id,
                                      updated_user=updated_user)
    except UserAlreadyExistsError:
       raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail='User with this username - already exists'
        )
    except UserNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )


@users_router.delete('/delete/{user_id}')
async def delete_one(user_id: Annotated[int, Path()]):
    try: 
        await user_service.delete_one(user_id=user_id)
    except UserNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    except PublisherCantConnectToBrokerError:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Unable to delete user, please try again later'
        )
    