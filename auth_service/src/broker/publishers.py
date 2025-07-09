import json
import asyncio
from uuid import UUID
from typing import Self

from aio_pika import Message
from aio_pika.abc import (
    AbstractChannel, AbstractConnection, 
    AbstractIncomingMessage
)

from exceptions.broker import (
    PublisherCantConnectToBrokerError,
    PublisherTimeoutReceivingResponseError
)
from broker.connection import (
    get_connection_to_broker,
    close_connection_to_broker
)
from core.settings import USER_CREATION_QUEUE_NAME
from logger import logger


class UserCreationPublisher:
    """
    UserCreationPublisher is a context manager which publish a message on user creation.
    It opens connection to broker and after message publishing - closes it.
    """
    user_creation_reply_queue_name = 'amq.rabbitmq.reply-to'

    def __init__(self) -> None:
        self.connection: AbstractConnection | None = None
        self.channel: AbstractChannel | None = None
        
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
        if not (self.channel and self.channel.is_closed):
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(
                USER_CREATION_QUEUE_NAME,
                durable=True
            )
        logger.info("Publisher has connected to queue")
        return self.channel
    
    async def publish_and_get_created_user_id(self, data: bytes) -> UUID:
        """Publishes message and waits for reply with created user`s id"""
        channel = await self._get_channel()
        reply_queue = await channel.get_queue(self.user_creation_reply_queue_name)

        # subscribing on reply queue
        message_queue = asyncio.Queue(maxsize=1)
        consumer_tag = await reply_queue.consume(
            callback=message_queue.put,
            no_ack=True
        )

        await channel.default_exchange.publish(
            message=Message(
                data,
                reply_to=self.user_creation_reply_queue_name
            ),
            routing_key=USER_CREATION_QUEUE_NAME,
        )
        logger.info("Publish message on user creation")

        # wait for message throught reply queue
        try:
            response: AbstractIncomingMessage = await asyncio.wait_for(message_queue.get(),
                                                                       timeout=4)
            new_user_id: UUID = json.loads(response.body)['new_user_id']
        except asyncio.TimeoutError as e:
            logger.warning('Publisher didn`t wait for a response')
            raise PublisherTimeoutReceivingResponseError(
                "Publisher was waiting for a response from consumer too long"
            ) from e

        # clear queue
        await reply_queue.cancel(consumer_tag)
        logger.info('Publisher received response from cosumer')

        return new_user_id
