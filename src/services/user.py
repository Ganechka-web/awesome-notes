from shemas.user import (
    UserOutputShema,
    UserCreateShema
) 
from models.user import User
from repositories.user import UserRepository


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_all(self) -> list[UserOutputShema]: 
        users = await self.repository.get_all()

        return [UserOutputShema.model_validate(user)
                for user in users]
    
    async def get_one_by_id(self, id: int) -> UserOutputShema | None:
        user = await self.repository.get_one_by_id(id=id)

        return UserCreateShema.model_validate(user)
    
    async def get_one_by_username(self, 
                                  username: str) -> UserOutputShema | None:
        user = await self.repository.get_one_by_username(username=username)

        return UserCreateShema.model_validate(user)

    async def create_one(self, new_user: UserCreateShema) -> int:
        new_user_orm = User(**new_user.__dict__)
        new_user_id = await self.repository.create_one(user=new_user_orm)

        return new_user_id