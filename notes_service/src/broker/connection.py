from aio_pika import connect
from aio_pika.abc import AbstractConnection
from aio_pika.exceptions import AMQPConnectionError

from core.settings import rabbitmq_settings, DELETE_NOTES_QUEUE_NAME
from broker.callbacks import delete_all_user_notes_handler
from logger import logger


async def connect_to_broker() -> AbstractConnection:
    """Connects to message broker and starts consuming"""
    try:
        connection = await connect(
            host=rabbitmq_settings.host,
            port=rabbitmq_settings.port,
            login=rabbitmq_settings.user,
            password=rabbitmq_settings.password
        )
        logger.info("Message broker has connected successfully")
    except (AMQPConnectionError, ConnectionRefusedError):
        logger.critical("Connection to message broker failed")
        return

    # declare channel and queue
    channel = await connection.channel()
    delete_existing_notes_queue = await channel.declare_queue(
        DELETE_NOTES_QUEUE_NAME,
        durable=True
    )

    logger.info("Starting consuming...")

    # starts consuming
    await delete_existing_notes_queue.consume(callback=delete_all_user_notes_handler)

    return connection


async def close_connection_to_broker(connection: AbstractConnection | None) -> None:
    if not connection or connection.is_closed:
        logger.critical("Message broker hasn`t been connected, shutting down failed")
        return 
    
    await connection.close()
    logger.info("Message broker has shut down successfully")
