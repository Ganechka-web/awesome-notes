import json
import uuid
from unittest import mock
from typing import TYPE_CHECKING, Generator, AsyncGenerator, Callable

import pytest
import pytest_asyncio
from testcontainers.rabbitmq import RabbitMqContainer
from dependency_injector import providers

from src.core.settings import rabbitmq_settings, DELETE_NOTES_QUEUE_NAME
from src.broker.callbacks import DeleteAllUserNotesCallback

if TYPE_CHECKING:
    from src.core.broker import AsyncBroker


@pytest.fixture(scope="session")
def rabbitmq_container(container) -> Generator[RabbitMqContainer, None, None]:
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
async def note_broker(
    rabbitmq_container, container
) -> AsyncGenerator["AsyncBroker", None]:
    async_broker = container.note_broker()
    yield async_broker
    await async_broker.shutdown()


@pytest_asyncio.fixture(scope="function")
async def unrteachable_broker(container) -> AsyncGenerator["AsyncBroker", None]: 
    container.config.set(
        "rabbitmq_settings.host", "unreachable"
    )
    container.reset_singletons()
    broker = container.note_broker()
    yield broker
    await broker.shutdown()


@pytest.fixture(scope="session")
def mock_note_service(container) -> Generator[mock.AsyncMock, None, None]:
    container.note_service.override(mock.AsyncMock())
    yield container.note_service()
    container.note_service.reset_override()


@pytest.fixture
def delete_all_user_notes_callback(container) -> "DeleteAllUserNotesCallback":
    callback = container.delete_all_user_notes_callback()
    return callback


@pytest_asyncio.fixture
async def publish_message_in_delete_notes_queue(note_broker) -> Callable:
    async def wrapper(user_id: uuid.UUID) -> None:
        await note_broker.publish(
            data=json.dumps({"user_id": user_id.hex}).encode(encoding="utf-8"),
            queue_name=DELETE_NOTES_QUEUE_NAME,
            durable=True,
        )

    return wrapper
