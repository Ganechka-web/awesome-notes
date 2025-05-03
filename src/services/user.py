from shemas.user import (
    UserOutputShema,
    UserCreateShema,
    UserUpgrateShema
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

        return UserOutputShema.model_validate(user)
    
    async def get_one_by_username(self, 
                                  username: str) -> UserOutputShema | None:
        user = await self.repository.get_one_by_username(username=username)

        return UserOutputShema.model_validate(user)

    async def create_one(self, new_user: UserCreateShema) -> int:
        new_user_orm = User(**new_user.__dict__)
        new_user_id = await self.repository.create_one(user=new_user_orm)

        return new_user_id
    
    async def update_one(self, user_id: int, 
                         updated_user: UserUpgrateShema) -> None:
        current_user = await self.repository.get_one_by_id(id=user_id)
        for field, value in updated_user.model_dump(exclude_unset=True).items():
            setattr(current_user, field, value)

        await self.repository.update_one(user=current_user)

    async def delete_one(self, user_id) -> None:
        user_on_delete = await self.repository.get_one_by_id(id=user_id)
        await self.repository.delete_one(user=user_on_delete) 
