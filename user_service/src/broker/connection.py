from aio_pika import connect
from aio_pika.exceptions import AMQPConnectionError
from aio_pika.abc import AbstractConnection

from core.settings import rabbitmq_settings
from logger import logger


async def get_connection_to_broker() -> AbstractConnection | None:
    """Creates connection to broker and returns it"""
    try:
        connection = await connect(
            host=rabbitmq_settings.host,
            port=rabbitmq_settings.port,
            login=rabbitmq_settings.user,
            password=rabbitmq_settings.password
        )
        logger.info("Message broker has connected successfully")
        return connection
    except (AMQPConnectionError, ConnectionRefusedError):
        logger.critical("Connection to message broker failed")


async def close_connection_to_broker(connection: AbstractConnection) -> None:
    """Closes connection if it is active"""
    if not connection or connection.is_closed:
        logger.critical("Message broker hasn`t been connected, shutting down failed")
        return

    await connection.close()
    logger.info("Message broker has shut down successfully")
