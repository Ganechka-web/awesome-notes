import uuid
from unittest import mock

import pytest

from src.exceptions.service import NoteNotFoundError, NoteAlreadyExistsError


@pytest.mark.parametrize(
    ("md_content_format",),
    (
        (False,),
        (True,),
    ),
)
def test_get_all(md_content_format, mock_note_service, expected_notes_sch_with, client):
    expected_notes = expected_notes_sch_with(amount=10)
    mock_note_service.get_all = mock.AsyncMock(return_value=expected_notes)

    response = client.get("/note/", params={"md_content_format": md_content_format})

    assert response.status_code == 200
    mock_note_service.get_all.assert_awaited_once_with(
        md_content_format=md_content_format
    )

    for exp_note, res_note in zip(expected_notes, response.json()):
        assert exp_note.id == uuid.UUID(res_note["id"])
        assert exp_note.title == res_note["title"]
        assert exp_note.content == res_note["content"]
        assert exp_note.owner_id == uuid.UUID(res_note["owner_id"])


@pytest.mark.parametrize(
    ("md_content_format",),
    (
        (False,),
        (True,),
    ),
)
def test_get_all_empty(md_content_format, mock_note_service, client):
    mock_note_service.get_all = mock.AsyncMock(return_value=[])

    response = client.get("/note/", params={"md_content_format": md_content_format})

    assert response.status_code == 200
    mock_note_service.get_all.assert_awaited_once_with(
        md_content_format=md_content_format
    )
    assert response.json() == []


@pytest.mark.parametrize(
    ("owner_id", "md_content_format"),
    (
        (uuid.uuid4(), False),
        (uuid.uuid4(), True),
    ),
)
def test_get_all_by_owner_id(
    owner_id, md_content_format, mock_note_service, expected_notes_sch_with, client
):
    expected_notes = expected_notes_sch_with(owner_id=owner_id, amount=5)
    mock_note_service.get_all_by_owner_id = mock.AsyncMock(return_value=expected_notes)

    response = client.get(
        f"/note/by-owner-id/{owner_id.hex}",
        params={"md_content_format": md_content_format},
    )

    assert response.status_code == 200
    mock_note_service.get_all_by_owner_id.assert_awaited_once_with(
        owner_id=owner_id, md_content_format=md_content_format
    )

    for exp_note, res_note in zip(expected_notes, response.json()):
        assert exp_note.id == uuid.UUID(res_note["id"])
        assert exp_note.title == res_note["title"]
        assert exp_note.content == res_note["content"]
        assert exp_note.owner_id == uuid.UUID(res_note["owner_id"])


@pytest.mark.parametrize(
    ("owner_id", "md_content_format"),
    (
        (uuid.uuid4(), False),
        (uuid.uuid4(), True),
    ),
)
def test_get_all_by_owner_id_empty(
    owner_id, md_content_format, mock_note_service, client
):
    mock_note_service.get_all_by_owner_id = mock.AsyncMock(return_value=[])

    response = client.get(
        f"/note/by-owner-id/{owner_id.hex}",
        params={"md_content_format": md_content_format},
    )

    assert response.status_code == 200
    mock_note_service.get_all_by_owner_id.assert_awaited_once_with(
        owner_id=owner_id, md_content_format=md_content_format
    )
    assert response.json() == []


@pytest.mark.parametrize(
    ("id", "md_content_format"), ((uuid.uuid4(), False), (uuid.uuid4(), True))
)
def test_get_one_by_id(
    id, md_content_format, mock_note_service, expected_notes_sch_with, client
):
    expected_note = expected_notes_sch_with(id=id, amount=1)
    mock_note_service.get_one_by_id = mock.AsyncMock(return_value=expected_note)

    response = client.get(
        f"/note/by-id/{id.hex}", params={"md_content_format": md_content_format}
    )

    assert response.status_code == 200
    mock_note_service.get_one_by_id.assert_awaited_once_with(
        note_id=id, md_content_format=md_content_format
    )

    res_note = response.json()
    assert uuid.UUID(res_note["id"]) == expected_note.id
    assert res_note["title"] == expected_note.title
    assert res_note["content"] == expected_note.content
    assert uuid.UUID(res_note["owner_id"]) == expected_note.owner_id


@pytest.mark.parametrize(
    ("id", "md_content_format"), ((uuid.uuid4(), False), (uuid.uuid4(), True))
)
def test_get_one_by_id_not_found(id, md_content_format, mock_note_service, client):
    mock_note_service.get_one_by_id = mock.AsyncMock(
        side_effect=NoteNotFoundError("...")
    )

    response = client.get(
        f"/note/by-id/{id.hex}", params={"md_content_format": md_content_format}
    )

    assert response.status_code == 404
    mock_note_service.get_one_by_id.assert_awaited_once_with(
        note_id=id, md_content_format=md_content_format
    )
    assert "detail" in response.json()


@pytest.mark.parametrize(
    ("title", "content", "owner_id"),
    (
        ("Note_title_1", "# Note md content", uuid.uuid4()),
        ("Note_title_2", "[Google.com link][https://www.google.com]", uuid.uuid4()),
    ),
)
def test_create_one_success(title, content, owner_id, mock_note_service, client):
    created_note_id = uuid.uuid4()
    create_data = {"title": title, "content": content, "owner_id": owner_id.hex}
    mock_note_service.create_one = mock.AsyncMock(return_value=created_note_id)

    response = client.post("/note/create/", json=create_data)

    assert response.status_code == 201
    mock_note_service.create_one.assert_awaited_once()

    called_note_sch = mock_note_service.create_one.call_args.kwargs["new_note"]
    assert called_note_sch.title == create_data["title"]
    assert called_note_sch.content == create_data["content"]
    assert called_note_sch.owner_id == uuid.UUID(create_data["owner_id"])


def test_create_one_already_exists(mock_note_service, client):
    create_data = {
        "title": "some title",
        "content": "# some md content",
        "owner_id": uuid.uuid4().hex,
    }
    mock_note_service.create_one = mock.AsyncMock(
        side_effect=NoteAlreadyExistsError("...")
    )

    response = client.post("/note/create/", json=create_data)

    assert response.status_code == 409
    mock_note_service.create_one.assert_awaited_once()

    called_note_sch = mock_note_service.create_one.call_args.kwargs["new_note"]
    assert called_note_sch.title == create_data["title"]
    assert called_note_sch.content == create_data["content"]
    assert called_note_sch.owner_id == uuid.UUID(hex=create_data["owner_id"])


@pytest.mark.parametrize(
    ("id", "title", "content", "owner_id"),
    (
        (uuid.uuid4(), "Edited title_1", "# Some edited md", uuid.uuid4()),
        (uuid.uuid4(), "Edited only title_2", None, None),
        (uuid.uuid4(), None, "# Some only edited md", None),
        (uuid.uuid4(), None, None, uuid.uuid4()),
    ),
)
def test_update_one_success(id, title, content, owner_id, mock_note_service, client):
    update_data = {
        "title": title,
        "content": content,
        "owner_id": owner_id.hex if owner_id else None,
    }
    mock_note_service.update_one = mock.AsyncMock(return_value=None)

    response = client.patch(f"/note/update/{id}", json=update_data)

    assert response.status_code == 200
    mock_note_service.update_one.assert_awaited_once()

    called_id = mock_note_service.update_one.call_args.kwargs["note_id"]
    assert called_id == id

    called_note_sch = mock_note_service.update_one.call_args.kwargs["updated_note"]
    assert called_note_sch.title == update_data["title"]
    assert called_note_sch.content == update_data["content"]
    if owner_id:
        assert called_note_sch.owner_id == uuid.UUID(update_data["owner_id"])


@pytest.mark.parametrize(
    ("raised_exception", "status_code"),
    (
        (NoteNotFoundError("..."), 404),
        (NoteAlreadyExistsError("..."), 409),
    ),
)
def test_update_one_failed(raised_exception, status_code, mock_note_service, client):
    updated_note_id = uuid.uuid4()
    update_data = {
        "title": "edited_title",
        "content": "### Edited md content",
        "owner_id": uuid.uuid4().hex,
    }
    mock_note_service.update_one = mock.AsyncMock(side_effect=raised_exception)

    response = client.patch(f"/note/update/{updated_note_id.hex}", json=update_data)

    assert response.status_code == status_code
    mock_note_service.update_one.assert_awaited_once()

    called_id = mock_note_service.update_one.call_args.kwargs["note_id"]
    assert called_id == updated_note_id

    called_note_sch = mock_note_service.update_one.call_args.kwargs["updated_note"]
    assert called_note_sch.title == update_data["title"]
    assert called_note_sch.content == update_data["content"]
    assert called_note_sch.owner_id == uuid.UUID(update_data["owner_id"])


def test_delete_one_success(mock_note_service, client):
    note_on_delete_id = uuid.uuid4()
    mock_note_service.delete_one = mock.AsyncMock(return_value=None)

    response = client.delete(f"/note/delete/{note_on_delete_id.hex}")

    assert response.status_code == 204
    mock_note_service.delete_one.assert_awaited_once_with(note_id=note_on_delete_id)


def test_delete_one_success_unexists(mock_note_service, client):
    note_on_delete_id = uuid.uuid4()
    mock_note_service.delete_one = mock.AsyncMock(side_effect=NoteNotFoundError("..."))

    response = client.delete(f"/note/delete/{note_on_delete_id.hex}")

    assert response.status_code == 404
    mock_note_service.delete_one.assert_awaited_once_with(note_id=note_on_delete_id)


def test_delete_all_by_owner_id(mock_note_service, client):
    owner_id = uuid.uuid4()
    mock_note_service.delete_all_by_owner_id = mock.AsyncMock(return_value=None)


    response = client.delete(f"/note/delete/by-owner-id/{owner_id.hex}") 

    assert response.status_code == 204
    mock_note_service.delete_all_by_owner_id.assert_awaited_once_with(owner_id=owner_id)

