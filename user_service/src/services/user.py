import json

from shemas.user import (
    UserOutputShema,
    UserCreateShema,
    UserUpgrateShema
) 
from models.user import User
from repositories.user import UserRepository
from exceptions.repositories import DataBaseError
from exceptions.services import ( 
    UserNotFoundError, 
    UserAlreadyExistsError
)
from broker.publishers import NotePublisher
from exceptions.broker import PublisherCantConnectToBrokerError
from logger import logger


class UserService:
    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_all(self) -> list[UserOutputShema]: 
        users = await self.repository.get_all()

        return [UserOutputShema.model_validate(user)
                for user in users]
    
    async def get_one_by_id(self, id: int) -> UserOutputShema | None:
        try:
            user = await self.repository.get_one_by_id(id=id)
        except DataBaseError as e:
            raise UserNotFoundError(
                f'Unable to find user with id - {id}'
            ) from e

        return UserOutputShema.model_validate(user)
    
    async def get_one_by_username(self, 
                                  username: str) -> UserOutputShema | None:
        try:
            user = await self.repository.get_one_by_username(username=username)
        except DataBaseError as e:
            raise UserNotFoundError(
                f'Unable to find user with username - {username}'
            ) from e

        return UserOutputShema.model_validate(user)

    async def create_one(self, new_user: UserCreateShema) -> int:
        new_user_orm = User(**new_user.__dict__)
        try:
            new_user_id = await self.repository.create_one(user=new_user_orm)
        except DataBaseError as e:
            raise UserAlreadyExistsError(
                f'User with username - {new_user.username} already exists'
            ) from e

        return new_user_id
    
    async def update_one(self, user_id: int, 
                         updated_user: UserUpgrateShema) -> None:
        try: 
            current_user = await self.repository.get_one_by_id(id=user_id)
        except DataBaseError as e:
            raise UserNotFoundError(
                f'Unable to find user with id - {user_id}'
            ) from e
        
        for field, value in updated_user.model_dump(exclude_unset=True).items():
            setattr(current_user, field, value)

        try:
            await self.repository.update_one(user=current_user)
        except DataBaseError as e:
            raise UserAlreadyExistsError(
                f'User with username - {updated_user.username} already exists'
            ) from e

    async def delete_one(self, user_id) -> None:
        try: 
            user_on_delete = await self.repository.get_one_by_id(id=user_id)
        except DataBaseError as e:
            raise UserNotFoundError(
                f'Unable to find user with id - {user_id}'
            ) from e
        
        # create and publish message for deleting all user`s notes
        try:
            async with NotePublisher() as notes_publisher:    
                data = bytes(
                    json.dumps({'user_id': user_id}),
                    encoding='utf-8'
                )
                await notes_publisher.publish(data=data)
        except PublisherCantConnectToBrokerError:
            logger.warning("Unable to send message, publisher unavailable")
            raise 

        await self.repository.delete_one(user=user_on_delete) 
