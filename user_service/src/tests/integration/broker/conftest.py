import uuid
import asyncio
from typing import TYPE_CHECKING, Generator, AsyncGenerator, Callable
from unittest import mock

import pytest
import pytest_asyncio
from testcontainers.rabbitmq import RabbitMqContainer
from aio_pika.abc import AbstractQueue, AbstractIncomingMessage

from src.core.settings import rabbitmq_settings

if TYPE_CHECKING:
    from src.core.broker import AsyncBroker
    from src.broker.callbacks import CreateUserCallback


@pytest.fixture(scope="session", autouse=True)
def rabbitmq_container(container) -> Generator[RabbitMqContainer, None, None]:
    """
    Starts RabbitMQ docker container, sets new container config variables.
    Stops container at the end
    """
    rabbitmq_cont = RabbitMqContainer(
        image="rabbitmq:4.1-management-alpine",
        port=rabbitmq_settings.port,
        username=rabbitmq_settings.user,
        password=rabbitmq_settings.password,
    )
    rabbitmq_cont.start()

    container.config.set(
        "rabbitmq_settings.host", rabbitmq_cont.get_container_host_ip()
    )
    container.config.set(
        "rabbitmq_settings.port", rabbitmq_cont.get_exposed_port(rabbitmq_settings.port)
    )
    container.reset_singletons()

    yield rabbitmq_cont

    rabbitmq_cont.stop()


@pytest_asyncio.fixture(scope="session")
async def user_broker(container) -> AsyncGenerator["AsyncBroker", None]:
    """Yields AsyncBroker instance"""
    broker = container.user_broker()
    yield broker
    await broker.shutdown()


@pytest_asyncio.fixture(scope="session")
async def user_broker_unreachable(
    container, rabbitmq_container
) -> AsyncGenerator["AsyncBroker", None]:
    """Yields unreachable AsyncBroker instance"""
    container.config.set("rabbitmq_settings.host", "unreachable_host")
    container.reset_singletons()
    broker = container.user_broker()

    yield broker

    await broker.shutdown()

    container.config.set(
        "rabbirmq_settings.host", rabbitmq_container.get_container_host_ip()
    )
    container.reset_singletons()


@pytest.fixture
def mock_user_service(container) -> Generator[mock.AsyncMock, None, None]:
    """Yields UserService mock"""
    container.user_service.override(mock.AsyncMock)
    yield container.user_service()
    container.user_service.reset_override()


@pytest.fixture
def create_user_callback(container) -> "CreateUserCallback":
    """Returns CreateUserCallback instance"""
    return container.create_user_callback()


class TestRPCClient:
    """Testing plub for immitation real RPC client"""

    def __init__(self, broker: "AsyncBroker") -> None:
        self.broker = broker
        self._replies: dict[str, asyncio.Future] = {}
        self._reply_queue: AbstractQueue | None = None
        self._reply_queue_name: str | None = None

    async def _create_reply_queue(self) -> None:
        """Creates reply_queue, sets up _reply_queue and _reply_queue_name"""
        if self._reply_queue is None:
            self._reply_queue = await self.broker._channel.declare_queue(exclusive=True)
            self._reply_queue_name = self._reply_queue.name
            await self._reply_queue.consume(callback=self.on_response)

    async def on_response(self, message: AbstractIncomingMessage) -> None:
        """Sets future`s result up according to mesage.correlation_id"""
        if message.correlation_id in self._replies:
            self._replies[message.correlation_id].set_result(message.body)
            await message.ack()

    async def call(self, queue_name: str, data: bytes) -> bytes:
        """Punlishes a message and waits for reply"""
        await self._create_reply_queue()
        properties = {
            "reply_to": self._reply_queue_name,
            "correlation_id": str(uuid.uuid4()),
        }
        await self.broker.publish(queue_name=queue_name, data=data, **properties)

        current_reply_future = asyncio.Future()
        self._replies[properties["correlation_id"]] = current_reply_future

        return await asyncio.wait_for(current_reply_future, timeout=3)


@pytest_asyncio.fixture
async def call_rpc_client(user_broker) -> Callable:
    """Creates RPC client instance, calls it and return result"""

    async def inner(queue_name: str, data: bytes) -> bytes:
        rpc_client = TestRPCClient(broker=user_broker)
        reply = await rpc_client.call(queue_name=queue_name, data=data)
        return reply

    return inner
