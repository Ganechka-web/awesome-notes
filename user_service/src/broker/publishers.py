from typing import Self

from aio_pika import Message
from aio_pika.abc import AbstractConnection, AbstractChannel

from core.settings import DELETE_NOTES_QUEUE_NAME
from exceptions.broker import PublisherCantConnectToBrokerError
from broker.connection import (
    get_connection_to_broker,
    close_connection_to_broker
)
from logger import logger


class NotePublisher:
    """
    NotePublisher is an context manager to publish message to delete user`s notes.
    It opens connection and after message publishing, closes connection. 
    """
    def __init__(self) -> None:
        self.connection: AbstractConnection = None
        self.channel: AbstractChannel = None

    async def __aenter__(self) -> Self:
        self.connection = await get_connection_to_broker()
        if self.connection is None:
            logger.warning("Publisher can`t connect to broker")
            raise PublisherCantConnectToBrokerError(
                "Publisher can`t connect to broker, broker not available"
            )
        logger.info("Publisher has opened connection")
        return self
    
    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type:
            logger.warning(
                "Publisher has raised an exception during running: "
                f"type - {exc_type}, value - {exc_value}, "
                f"traceback - {traceback}"
            )
        await close_connection_to_broker(self.connection)
        logger.info("Publisher`s connection has closed")

    async def _get_channel(self) -> AbstractChannel:
        if not self.channel or self.channel.is_closed:
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(
                DELETE_NOTES_QUEUE_NAME, 
                durable=True
            )
        logger.info("Publisher has connected to queue")
        return self.channel
    
    async def publish(self, data: bytes) -> None:
        channel = await self._get_channel()
        await channel.default_exchange.publish(
            message=Message(data),
            routing_key=DELETE_NOTES_QUEUE_NAME
        )
        logger.info("Publish message on delete user`s notes")
