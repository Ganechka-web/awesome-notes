import json
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from aio_pika.abc import AbstractIncomingMessage

from logger import logger

if TYPE_CHECKING:
    from services.note import NoteService


class BaseCallback(ABC):
    @abstractmethod
    async def handle(self, message: AbstractIncomingMessage):
        raise NotImplementedError


class DeleteAllUserNotesCallback(BaseCallback):
    """Callback for receiving messages to delete user`s notes"""

    def __init__(self, note_service: "NoteService") -> None:
        self.note_service = note_service

    async def handle(self, message: AbstractIncomingMessage) -> None:
        logger.info("Received messege on delete user`s notes")
        user_id = json.loads(message.body)["user_id"]

        await self.note_service.delete_all_by_owner_id(owner_id=user_id)
        await message.ack()

        logger.info("Message has processed successfully")
