import uuid
import asyncio
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from src.core.settings import DELETE_NOTES_QUEUE_NAME
from src.exceptions.broker import UnableToConnectToBrokerError

if TYPE_CHECKING:
    from src.broker.callbacks import DeleteAllUserNotesCallback
    from src.core.broker import AsyncBroker


@pytest.mark.asyncio
async def test_delete_all_user_notes(
    publish_message_in_delete_notes_queue,
    mock_note_service: mock.AsyncMock,
    delete_all_user_notes_callback: "DeleteAllUserNotesCallback",
    note_broker: "AsyncBroker",
):
    user_id = uuid.uuid4()
    mock_note_service.delete_all_by_owner_id.return_value = None

    await note_broker.consume(
        queue_name=DELETE_NOTES_QUEUE_NAME, callback=delete_all_user_notes_callback
    )
    await publish_message_in_delete_notes_queue(user_id=user_id)

    # waiting for consuming handler call processed
    await asyncio.sleep(4)

    mock_note_service.delete_all_by_owner_id.assert_awaited_once_with(owner_id=user_id.hex)
    

@pytest.mark.asyncio
async def test_delete_all_user_notes_unreachable_broker(
    publish_message_in_delete_notes_queue,
    delete_all_user_notes_callback: "DeleteAllUserNotesCallback",
    unrteachable_broker: "AsyncBroker",
):
    with pytest.raises(UnableToConnectToBrokerError):
        user_id = uuid.uuid4()
        await unrteachable_broker.consume(
            queue_name=DELETE_NOTES_QUEUE_NAME, callback=delete_all_user_notes_callback
        )
        await publish_message_in_delete_notes_queue(user_id=user_id)
