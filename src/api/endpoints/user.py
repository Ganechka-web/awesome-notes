from typing import Annotated

from fastapi import APIRouter, Path

from core.database import async_engine
from repositories.user import UserRepository
from services.user import UserService
from shemas.user import (
    UserOutputShema, 
    UserCreateShema,
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
    user = await user_service.get_one_by_id(id=user_id)

    return user


@users_router.get('/by-username/{username}')
async def get_one_by_username(username: Annotated[str, Path()]) -> UserOutputShema:
    user = await user_service.get_one_by_username(username=username)

    return user

@users_router.post('/create/')
async def create_one(new_user: UserCreateShema):
    new_user_id = await user_service.create_one(new_user=new_user)

    return new_user_id


@users_router.patch('/update/{user_id}')
async def update_one(user_id: Annotated[int, Path()], 
                     updated_user: UserUpgrateShema):
    await user_service.update_one(user_id=user_id,
                                  updated_user=updated_user)


@users_router.delete('/delete/{user_id}')
async def delete_one(user_id: Annotated[int, Path()]):
    await user_service.delete_one(user_id=user_id)
    