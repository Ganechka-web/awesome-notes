import uuid
import json
from typing import TYPE_CHECKING, Callable
from unittest import mock

import pytest

from src.core.settings import USER_CREATION_QUEUE_NAME
from src.exceptions.broker import UnableToConnectToBrokerError
from src.exceptions.services import UserAlreadyExistsError
from src.shemas.integration_errors import UserServiceCreationErrorSchema

if TYPE_CHECKING:
    from src.broker.callbacks import CreateUserCallback
    from src.core.broker import AsyncBroker


@pytest.mark.asyncio
async def test_create_user_callback(
    mock_user_service: mock.AsyncMock,
    call_rpc_client: Callable,
    user_broker: "AsyncBroker",
    create_user_callback: "CreateUserCallback",
):
    created_user_id = uuid.uuid4()
    user_on_create_data = {"username": "Some_username", "gender": "male", "age": 24}
    user_on_create_data_binary = json.dumps(user_on_create_data).encode(
        encoding="utf-8"
    )
    mock_user_service.create_one = mock.AsyncMock(return_value=created_user_id)

    await user_broker.consume(
        queue_name=USER_CREATION_QUEUE_NAME, callback=create_user_callback
    )

    reply_from_rpc_client = await call_rpc_client(
        queue_name=USER_CREATION_QUEUE_NAME, data=user_on_create_data_binary
    )

    assert (
        uuid.UUID(json.loads(reply_from_rpc_client)["created_user_id"])
        == created_user_id
    )

    mock_user_service.create_one.assert_awaited_once()
    called_user_sch = mock_user_service.create_one.call_args.kwargs["new_user"]
    assert called_user_sch.username == user_on_create_data["username"]
    assert called_user_sch.gender == user_on_create_data["gender"]
    assert called_user_sch.age == user_on_create_data["age"]


@pytest.mark.asyncio
async def test_create_user_callback_already_exists(
    mock_user_service: mock.AsyncMock,
    call_rpc_client: Callable,
    user_broker: "AsyncBroker",
    create_user_callback: "CreateUserCallback",
):
    user_on_create_data = {"username": "Some_username", "gender": "male", "age": 24}
    user_on_create_data_binary = json.dumps(user_on_create_data).encode(
        encoding="utf-8"
    )
    user_service_error_message = "Some_text_about_error"
    mock_user_service.create_one = mock.AsyncMock(
        side_effect=UserAlreadyExistsError(user_service_error_message)
    )

    await user_broker.consume(
        queue_name=USER_CREATION_QUEUE_NAME, callback=create_user_callback
    )

    reply_from_rpc_client = json.loads(
        await call_rpc_client(
            queue_name=USER_CREATION_QUEUE_NAME, data=user_on_create_data_binary
        )
    )

    error_from_user_service = UserServiceCreationErrorSchema.model_validate(
        json.loads(reply_from_rpc_client["error"])
    )
    assert error_from_user_service.message == user_service_error_message
    assert error_from_user_service.service_name == "user_service"
    assert error_from_user_service.http_status_code == 409

    mock_user_service.create_one.assert_awaited_once()
    called_user_sch = mock_user_service.create_one.call_args.kwargs["new_user"]
    assert called_user_sch.username == user_on_create_data["username"]
    assert called_user_sch.gender == user_on_create_data["gender"]
    assert called_user_sch.age == user_on_create_data["age"]


@pytest.mark.asyncio
async def test_create_user_callback_unreachable_broker(
    user_broker_unreachable: "AsyncBroker",
    create_user_callback: "CreateUserCallback",
):
    with pytest.raises(UnableToConnectToBrokerError):
        await user_broker_unreachable.consume(
            queue_name=USER_CREATION_QUEUE_NAME, callback=create_user_callback
        )
