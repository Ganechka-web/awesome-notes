from aio_pika import connect
from aio_pika.abc import AbstractConnection

from core.settings import rabbitmq_settings, DELETE_NOTES_QUEUE_NAME
from broker.callbacks import delete_all_user_notes_handler


connection: AbstractConnection


async def connect_to_broker() -> None:
    """Connects to nessage broker and starts consuming"""
    global connection
    connection = await connect(
        host=rabbitmq_settings.host,
        port=rabbitmq_settings.port,
        login=rabbitmq_settings.user,
        password=rabbitmq_settings.password
    )

    # declare channel and queue
    channel = await connection.channel()
    delete_existing_notes_queue = await channel.declare_queue(
        DELETE_NOTES_QUEUE_NAME,
        durable=True
    )

    # srarts consuming
    await delete_existing_notes_queue.consume(callback=delete_all_user_notes_handler)


async def close_connection_to_broker() -> None:
    if not connection.is_closed:
        global connection
        await connection.close()
