import json
from uuid import UUID
from typing import TYPE_CHECKING

from aio_pika.abc import AbstractIncomingMessage, AbstractChannel
from aio_pika import Message

from src.shemas.user import UserCreateShema
from src.shemas.integration_errors import UserServiceCreationErrorSchema
from src.exceptions.services import UserAlreadyExistsError
from src.logger import logger

if TYPE_CHECKING:
    from src.services.user import UserService


class CreateUserCallback:
    """CreateUserCallback is an class for message handing and sending reply with new entity id"""

    def __init__(self, user_service: "UserService"):
        self.user_service = user_service

    async def handle(
        self, message: AbstractIncomingMessage, channel: AbstractChannel
    ) -> None:
        logger.info("Received message on user creation")

        # create new user and get his id
        new_user_id: UUID = None
        error: UserServiceCreationErrorSchema = None
        try:
            user_schema = UserCreateShema.model_validate(json.loads(message.body))
            new_user_id = await self.user_service.create_one(new_user=user_schema)
        except UserAlreadyExistsError as err:
            error = UserServiceCreationErrorSchema(message=err.msg)

        # send message with created_user_id to reply queue
        if message.reply_to:
            await channel.default_exchange.publish(
                message=Message(
                    body=json.dumps(
                        {
                            "created_user_id": (
                                new_user_id.hex if new_user_id else new_user_id
                            ),
                            "error": error.model_dump_json() if error else None,
                        }
                    ).encode(encoding="utf-8"),
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )
        logger.info("Send reply message in reply_to queue")
