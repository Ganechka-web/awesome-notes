from typing import TYPE_CHECKING, Generator, AsyncGenerator, Callable

import pytest
import pytest_asyncio
from testcontainers.rabbitmq import RabbitMqContainer
from aio_pika import Message
from aio_pika.abc import AbstractIncomingMessage, AbstractChannel, ConsumerTag

from src.core.settings import rabbitmq_settings, USER_CREATION_QUEUE_NAME

if TYPE_CHECKING:
    from src.core.broker import AsyncBroker
    from src.broker.rpc_clients import UserCreationRPCClient


@pytest.fixture(scope="session", autouse=True)
def rabbitmq_container(container) -> Generator[RabbitMqContainer, None, None]:
    """
    Starts RabbitMQ test container in docker, sets new host and port in dependencies container
    """
    rabbitmq_container = RabbitMqContainer(
        image="rabbitmq:4.1-management-alpine",
        port=5672,
        username=rabbitmq_settings.user,
        password=rabbitmq_settings.password,
    )
    rabbitmq_container.start()

    container.config.set(
        "rabbitmq_settings.host", rabbitmq_container.get_container_host_ip()
    )
    container.config.set(
        "rabbitmq_settings.port", rabbitmq_container.get_exposed_port(5672)
    )
    container.reset_singletons()

    yield rabbitmq_container

    rabbitmq_container.stop()


@pytest_asyncio.fixture(scope="session")
async def auth_broker(
    container, rabbitmq_container
) -> AsyncGenerator["AsyncBroker", None]:
    auth_broker = container.auth_broker()
    yield auth_broker
    await auth_broker.shutdown()


@pytest.fixture(scope="function")
def user_creation_rpc_client(container, auth_broker) -> "UserCreationRPCClient":
    return container.user_creation_rpc_client()


@pytest.fixture(scope="function")
def user_creation_rpc_client_with_unreachable_broker(
    container,
) -> "UserCreationRPCClient":
    """Returns RPC with an unreachable broker via container"""
    container.config.set("rabbitmq_settings.host", "unreachable")
    container.reset_singletons()
    return container.user_creation_rpc_client()


class TestCallback:
    """
    TestCallback is a test callback for consuming messages and sending reply while testing
    """

    __slots__ = ("reply_data",)

    def __init__(self, reply_data: bytes):
        self.reply_data = reply_data

    async def handle(
        self, message: AbstractIncomingMessage, channel: AbstractChannel
    ) -> None:
        if message.reply_to:
            await channel.default_exchange.publish(
                message=Message(
                    body=self.reply_data,
                    correlation_id=message.correlation_id,
                ),
                routing_key=message.reply_to,
            )


@pytest_asyncio.fixture
async def start_consuming_ucq(user_creation_rpc_client) -> Callable:
    """
    Starts consuming messages from USER_CREATION_QUEUE via TestCallback.
    Returns consumer tag
    """

    async def wrapper(reply_data: bytes) -> ConsumerTag:
        test_callback = TestCallback(reply_data=reply_data)
        consumer_tag = await user_creation_rpc_client.broker.consume(
            queue_name=USER_CREATION_QUEUE_NAME, callback=test_callback
        )
        return consumer_tag

    return wrapper


@pytest_asyncio.fixture
async def stop_consuming_ucq(user_creation_rpc_client) -> Callable:
    """
    Stops consuming mesages from USER_CREATION_QUEUE according consumer tag
    """

    async def wrapper(consumer_tag: ConsumerTag) -> None:
        queue = await user_creation_rpc_client.broker._channel.get_queue(
            USER_CREATION_QUEUE_NAME
        )
        await queue.cancel(consumer_tag)

    return wrapper
