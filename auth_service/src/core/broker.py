from functools import partial

from aio_pika import connect, Message
from aio_pika.exceptions import AMQPConnectionError
from aio_pika.abc import AbstractConnection, AbstractChannel

from exceptions.broker import UnableToConnectToBrokerError
from logger import logger


class AsyncBroker:
    """Async broker is an class for managing broker connection, consuming and publishing"""

    def __init__(self, host: str, port: int, login: str, password: str) -> None:
        self.host = host
        self.port = port
        self.login = login
        self.password = password

        self._channel: AbstractChannel | None = None
        self._connection: AbstractConnection | None = None

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

    async def broker_set_up(self) -> None:
        """Sets broker connection and channel up"""
        if self._connection is None:
            await self._create_amqp_connection()
        if self._channel is None:
            await self._create_channel()

    async def consume(self, queue_name: str, callback) -> None:
        await self.broker_set_up()

        logger.info(f"Starting consuming messages from {queue_name} queue...")

        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.consume(callback=partial(callback.handle, channel=self._channel))

    async def publish(self, queue_name: str, data: bytes, **message_kwargs) -> None:
        await self.broker_set_up()

        message = Message(data, **message_kwargs)
        queue = await self._channel.declare_queue(queue_name, durable=True)
        await queue.channel.default_exchange.publish(
            message=message, routing_key=queue_name
        )

        logger.info(f"Publish message from {queue_name} queue")

    async def shutdown(self) -> None:
        if self._connection:
            await self._connection.close()
        if self._channel:
            await self._channel.close()
        logger.info("Message broker has shut down successfully")
