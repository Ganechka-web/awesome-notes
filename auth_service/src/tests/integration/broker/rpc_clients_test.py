import json
import uuid
from typing import TYPE_CHECKING

import pytest

from src.core.settings import USER_CREATION_QUEUE_NAME
from src.exceptions.broker import UnableToConnectToBrokerError

if TYPE_CHECKING:
    from src.broker.rpc_clients import UserCreationRPCClient


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("data", "reply"),
    (
        (
            {"username": "test_username", "gender": "male", "age": 27},
            {"created_user_id": uuid.uuid4().hex, "error": None},
        ),
        (
            {"username": "existed_username", "gender": "unknown", "age": 19},
            {
                "created_user_id": None,
                "error": {
                    "service_name": "user_service",
                    "http_status_code": 409,
                    "message": "some_error",
                },
            },
        ),
    ),
)
async def test_user_creation_rpc_client(
    data,
    reply,
    user_creation_rpc_client: "UserCreationRPCClient",
    start_consuming_ucq,
    stop_consuming_ucq,
):
    consumer_tag = await start_consuming_ucq(reply_data=json.dumps(reply).encode())

    reply_data = await user_creation_rpc_client.call(
        queue_name=USER_CREATION_QUEUE_NAME,
        data=json.dumps(data).encode(),
        timeout=20,
    )

    encoded_reply_data = json.loads(reply_data)
    assert encoded_reply_data["created_user_id"] == (
        reply["created_user_id"] if reply["created_user_id"] else None
    )
    assert encoded_reply_data["error"] == reply["error"]

    await stop_consuming_ucq(consumer_tag)


@pytest.mark.asyncio
async def test_user_creation_rpc_client_unreachable(
    user_creation_rpc_client_with_unreachable_broker,
):
    with pytest.raises(UnableToConnectToBrokerError):
        await user_creation_rpc_client_with_unreachable_broker.call(
            queue_name=USER_CREATION_QUEUE_NAME,
            data=json.dumps(
                {"username": "test_username", "gender": "female", "age": 46}
            ).encode(),
        )
