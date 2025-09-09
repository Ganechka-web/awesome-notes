import asyncio
from uuid import uuid4
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from aio_pika.abc import AbstractIncomingMessage, AbstractQueue

from src.exceptions.broker import ReceivingResponseTimeOutError
from src.logger import logger

if TYPE_CHECKING:
    from core.broker import AsyncBroker


class RPCClient(ABC):
    @abstractmethod
    async def on_response(self, message: AbstractIncomingMessage):
        raise NotImplementedError

    @abstractmethod
    async def call(self, queue_name: str, data: bytes, timeout: float = 5.0):
        raise NotImplementedError


class UserCreationRPCClient(RPCClient):
    """RPC client for sending message on user creation and then getting his id as a reply"""

    def __init__(self, broker: "AsyncBroker") -> None:
        self.broker = broker
        self._replies: dict[str, asyncio.Future] = {}
        self._reply_queue: AbstractQueue | None = None
        self._reply_queue_name: str | None = None

    async def _create_reply_queue(self) -> None:
        """Creates reply queue with using broker channel, sets up _reply_queue_name"""
        if self._reply_queue is None:
            await self.broker.broker_set_up()
            self._reply_queue = await self.broker._channel.declare_queue(exclusive=True)
            self._reply_queue_name = self._reply_queue.name
            await self._reply_queue.consume(callback=self.on_response)

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        """Sets Future result up by the message correlation_id"""
        if message.correlation_id in self._replies:
            self._replies[message.correlation_id].set_result(message.body)
            await message.ack()
            logger.info("RPC client has received response and processed it")

    async def call(self, queue_name: str, data: bytes, timeout: float = 5) -> bytes:
        """Publishes a message, and then waits for a response"""
        await self._create_reply_queue()
        properties = {
            "reply_to": self._reply_queue_name,
            "correlation_id": str(uuid4()),
        }
        await self.broker.publish(queue_name, data, **properties)

        current_reply_future = asyncio.Future()
        self._replies[properties["correlation_id"]] = current_reply_future

        try:
            logger.info("RPC client is waiting for response...")
            return await asyncio.wait_for(current_reply_future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("RPC client wasn`t waiting for response")
            raise ReceivingResponseTimeOutError("Receiving timeout expired")
