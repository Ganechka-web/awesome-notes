import json

from aio_pika.abc import AbstractIncomingMessage

from api.endpoints.note import note_service


async def delete_all_user_notes_handler(
    message: AbstractIncomingMessage
) -> None:
    """Callback for receiving measseges to delete user`s notes."""
    data = json.loads(message.body)
    await note_service.delete_all_by_owner_id(owner_id=data['user_id'])
    await message.ack()
