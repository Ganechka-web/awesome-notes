from aio_pika import connect
from aio_pika.abc import AbstractConnection

from core.settings import rabbitmq_settings


async def get_connection_to_broker() -> AbstractConnection:
    connection = await connect(
        host=rabbitmq_settings.host,
        port=rabbitmq_settings.port,
        login=rabbitmq_settings.user,
        password=rabbitmq_settings.password
    )
    return connection


async def close_connection_to_broker(connection: AbstractConnection) -> None:
    if not connection.is_closed:
        await connection.close()
    