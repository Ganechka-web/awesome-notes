from typing import TYPE_CHECKING

from aio_pika.abc import AbstractConnection, AbstractChannel
from aio_pika.exceptions import AMQPConnectionError
from aio_pika import connect, Message

from exceptions.broker import UnableToConnectToBrokerError
from logger import logger

if TYPE_CHECKING:
    from broker.callbacks import BaseCallback


class AsyncBroker:
    """Async broker is a class for managing broker connection and consuming"""

    def __init__(self, host: str, port: int, login: str, password: str):
        self.host = host
        self.port = port
        self.login = login
        self.password = password

        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None

    async def _create_amqp_connection(self) -> None:
        try:
            self._connection = await connect(
                host=self.host, port=self.port, login=self.login, password=self.password
            )
            logger.info("Message broker has connected successfully")
        except (AMQPConnectionError, ConnectionRefusedError):
            logger.critical("Connection to message broker failed")
            raise UnableToConnectToBrokerError("Unable to connect to message broker")

    async def _create_channel(self) -> None:
        self._channel = await self._connection.channel()

    async def consume(self, queue_name: str, callback: "BaseCallback") -> None:
        if self._connection is None:
            await self._create_amqp_connection()
        if self._channel is None:
            await self._create_channel()

        logger.info(f"Starting consuming messages from {queue_name} queue...")

        queue = await self._channel.declare_queue(name=queue_name, durable=True)
        await queue.consume(callback.handle)

    async def publish(self, queue_name: str, data: bytes) -> None:
        if self._connection is None:
            await self._create_amqp_connection()
        if self._channel is None:
            await self._create_channel()

        queue = await self._channel.declare_queue(name=queue_name)
        await queue._channel.default_exchange.publish(Message(data))

    async def shutdown(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
