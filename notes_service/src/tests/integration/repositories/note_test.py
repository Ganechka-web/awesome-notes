import uuid
from typing import TYPE_CHECKING

import pytest

from src.repositories.specifications import NotesForOwnerSpecification
from src.exceptions.repository import NoSuchRowError

if TYPE_CHECKING:
    from src.repositories.note import NoteRepository


@pytest.mark.asyncio
class TestNoteRepository:
    async def test_get_all_success(
        self, expected_data_with, insert_test_data, note_repository: "NoteRepository"
    ):
        expected_notes_on_insert, expected_notes_attrs = expected_data_with(amount=10)
        await insert_test_data(expected_notes_on_insert)

        notes = await note_repository.get_all()

        for exp_note, note in zip(expected_notes_attrs, notes):
            assert exp_note["id"] == note.id
            assert exp_note["title"] == note.title
            assert exp_note["content"] == note.content
            assert exp_note["owner_id"] == note.owner_id
            assert exp_note["created_at"] == note.created_at
            assert exp_note["updated_at"] == note.updated_at

    async def test_get_all_empty(self, note_repository: "NoteRepository"):
        notes = await note_repository.get_all()

        assert notes == []

    async def test_get_all_by_owner_id_success(
        self, expected_data_with, insert_test_data, note_repository: "NoteRepository"
    ):
        owner_id = uuid.uuid4()
        filtered_notes_amount = 3
        exp_notes_orm, _ = expected_data_with(amount=10)
        exp_notes_orm_with_owner_id, exp_notes_attrs_wirh_owner_id = expected_data_with(
            owner_id=owner_id, amount=filtered_notes_amount
        )
        await insert_test_data(exp_notes_orm)
        await insert_test_data(exp_notes_orm_with_owner_id)

        nfo_specification = NotesForOwnerSpecification(owner_id=owner_id)
        notes = await note_repository.filter_by(specification=nfo_specification)

        assert len(notes) == filtered_notes_amount
        for exp_note, note in zip(exp_notes_attrs_wirh_owner_id, notes):
            assert exp_note["id"] == note.id
            assert exp_note["title"] == note.title
            assert exp_note["content"] == note.content
            assert exp_note["owner_id"] == note.owner_id
            assert exp_note["created_at"] == note.created_at
            assert exp_note["updated_at"] == note.updated_at

    async def test_get_all_by_owner_id_empty(self, note_repository: "NoteRepository"):
        owner_id = uuid.uuid4()

        nfo_specification = NotesForOwnerSpecification(owner_id=owner_id)
        notes = await note_repository.filter_by(specification=nfo_specification)

        assert notes == []

    async def test_get_one_by_id(
        self, expected_data_with, insert_test_data, note_repository: "NoteRepository"
    ):
        expected_note_id = uuid.uuid4()
        exp_note_orm, exsp_note_attrs = expected_data_with(
            id=expected_note_id, amount=1
        )
        await insert_test_data(exp_note_orm)

        note = await note_repository.get_one_by_id(note_id=expected_note_id)

        assert exsp_note_attrs[0]["id"] == note.id
        assert exsp_note_attrs[0]["title"] == note.title
        assert exsp_note_attrs[0]["content"] == note.content
        assert exsp_note_attrs[0]["owner_id"] == note.owner_id

    async def test_get_one_by_id_unexists(self, note_repository: "NoteRepository"):
        expected_note_id = uuid.uuid4()
        with pytest.raises(NoSuchRowError):
            _ = await note_repository.get_one_by_id(note_id=expected_note_id)

    async def test_create_one(
        self, expected_data_with, note_repository: "NoteRepository"
    ):
        exp_note_orm, exp_note_attrs = expected_data_with(amount=1)
        del exp_note_orm[0].id
        del exp_note_attrs[0]["id"]

        created_note_id = await note_repository.create_one(note=exp_note_orm[0])

        assert isinstance(created_note_id, uuid.UUID)

        created_note = await note_repository.get_one_by_id(note_id=created_note_id)
        assert created_note.title == exp_note_attrs[0]["title"]
        assert created_note.content == exp_note_attrs[0]["content"]
        assert created_note.owner_id == exp_note_attrs[0]["owner_id"]

    @pytest.mark.parametrize(
        ("title", "content", "owner_id"),
        (
            ("updated_title", "### updated content", uuid.uuid4()),
            ("only_updated_title", None, None),
            (None, "[only][https://content] updated", None),
            (None, None, uuid.uuid4()),
            (None, None, None),
        ),
    )
    async def test_update_one(
        self,
        title,
        content,
        owner_id,
        expected_data_with,
        insert_test_data,
        note_repository: "NoteRepository",
    ):
        exp_note_id = uuid.uuid4()
        exp_note_orm, exp_note_attrs = expected_data_with(id=exp_note_id)
        await insert_test_data(exp_note_orm)

        if title:
            exp_note_orm[0].title = title
        if content:
            exp_note_orm[0].content = content
        if owner_id:
            exp_note_orm[0].owner_id = owner_id

        await note_repository.update_one(note=exp_note_orm[0])

        updated_note = await note_repository.get_one_by_id(note_id=exp_note_id)
        assert updated_note.title == title or exp_note_attrs[0]["title"]
        assert updated_note.content == content or exp_note_attrs[0]["content"]
        assert updated_note.owner_id == owner_id or exp_note_attrs[0]["owner_id"]

    async def test_delete_one(self, expected_data_with, insert_test_data, note_repository: "NoteRepository"):
        exp_note_id = uuid.uuid4()
        exp_note_orm, _ = expected_data_with(id=exp_note_id, amount=1)
        await insert_test_data(exp_note_orm)

        await note_repository.delete_one(note=exp_note_orm[0])
        
        with pytest.raises(NoSuchRowError):
            _ = await note_repository.get_one_by_id(note_id=exp_note_id)

    async def test_delete_all(self, expected_data_with, insert_test_data, note_repository: "NoteRepository"):
        exp_note_owner_id = uuid.uuid4()
        exp_notes_orm, _ = expected_data_with(owner_id=exp_note_owner_id, amount=3)
        exp_notes_orm_ids = [note.id for note in exp_notes_orm]
        await insert_test_data(exp_notes_orm)

        await note_repository.delete_all(exp_notes_orm_ids)

        specificatrion = NotesForOwnerSpecification(owner_id=exp_note_owner_id)
        notes = await note_repository.filter_by(specification=specificatrion)
        assert notes == []