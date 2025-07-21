import json
from uuid import UUID
from typing import TYPE_CHECKING

from aio_pika.abc import AbstractIncomingMessage, AbstractChannel
from aio_pika import Message

from shemas.user import UserCreateShema
from exceptions.services import UserAlreadyExistsError
from logger import logger

if TYPE_CHECKING:
    from services.user import UserService


class CreateUserCallback:
    """CreateUserCallback is an class for message handing and sending reply with new entity id"""

    def __init__(self, user_service: "UserService"):
        self.user_service = user_service

    async def handle(
        self, message: AbstractIncomingMessage, channel: AbstractChannel
    ) -> None:
        logger.info("Received message on user creation")

        # create new user and get his id
        new_user_id: UUID
        try:
            user_schema = UserCreateShema.model_validate(json.loads(message.body))
            new_user_id = await self.user_service.create_one(new_user=user_schema)
        except UserAlreadyExistsError:
            raise

        # send message with user_id to reply queue
        if message.reply_to:
            await channel.default_exchange.publish(
                message=Message(
                    body=json.dumps({"created_user_id": new_user_id.hex}).encode(
                        encoding="utf-8"
                    ),
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )
        logger.info("Send reply message in reply_to queue")
