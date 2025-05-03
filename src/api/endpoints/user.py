from fastapi import APIRouter

from core.database import async_engine
from repositories.user import UserRepository
from services.user import UserService
from shemas.user import UserOutputShema, UserCreateShema


users_router = APIRouter(prefix='/users')

user_repository = UserRepository(async_engine)
user_service = UserService(user_repository)


@users_router.get('/')
async def get_all() -> list[UserOutputShema]:
    users = await user_service.get_all()

    return users


@users_router.post('/create/')
async def create_one(new_user: UserCreateShema):
    new_user_id = await user_service.create_one(new_user=new_user)

    return new_user_id