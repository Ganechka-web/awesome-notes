import uuid
from unittest import mock

import markdown
import pytest

from src.exceptions.service import NoteNotFoundError, NoteAlreadyExistsError
from src.exceptions.repository import NoSuchRowError
from src.schemas.note import NoteCreateShema, NoteUpdateShema


class TestNoteService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("md_content_format",), ((True,), (False,)))
    async def test_get_all(
        self, md_content_format, mock_note_repository, expected_notes_with, note_service
    ):
        exp_notes_orm = expected_notes_with(amount=5)
        mock_note_repository.get_all = mock.AsyncMock(return_value=exp_notes_orm)

        notes = await note_service.get_all(md_content_format=md_content_format)

        for note_schema, note_orm in zip(notes, exp_notes_orm):
            mock_note_repository.get_all.assert_awaited_once()
            assert note_schema.id == note_orm.id
            assert note_schema.title == note_orm.title
            assert note_schema.content == (
                markdown.markdown(note_orm.content)
                if not md_content_format
                else note_orm.content
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("md_content_format",), ((True,), (False,)))
    async def test_get_all_empty(
        self, md_content_format, mock_note_repository, note_service
    ):
        mock_note_repository.get_all = mock.AsyncMock(return_value=[])

        notes = await note_service.get_all(md_content_format=md_content_format)

        mock_note_repository.get_all.assert_awaited_once()
        assert notes == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("owner_id", "md_content_format"), ((uuid.uuid4(), True), (uuid.uuid4(), False))
    )
    async def test_get_all_by_owner_id(
        self,
        owner_id,
        md_content_format,
        expected_notes_with,
        mock_note_repository,
        note_service,
    ):
        exp_notes_orm = expected_notes_with(owner_id=owner_id, amount=6)
        mock_note_repository.filter_by = mock.AsyncMock(return_value=exp_notes_orm)

        notes_by_owner_id = await note_service.get_all_by_owner_id(
            owner_id=owner_id, md_content_format=md_content_format
        )

        assert all(map(lambda nboi: nboi.owner_id == owner_id, notes_by_owner_id))
        mock_note_repository.filter_by.assert_awaited_once()
        for note_schema, note_orm in zip(notes_by_owner_id, exp_notes_orm):
            assert note_schema.content == (
                markdown.markdown(note_orm.content)
                if not md_content_format
                else note_orm.content
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("owner_id", "md_content_format"), ((uuid.uuid4(), True), (uuid.uuid4(), False))
    )
    async def test_get_all_by_owner_id_empty(
        self,
        owner_id,
        md_content_format,
        mock_note_repository,
        note_service,
    ):
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])

        notes_by_owner_id = await note_service.get_all_by_owner_id(
            owner_id=owner_id, md_content_format=md_content_format
        )

        assert notes_by_owner_id == []
        mock_note_repository.filter_by.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("md_content_format",), ((True,), (False,)))
    async def test_get_one_by_id(
        self,
        md_content_format,
        expected_notes_with,
        mock_note_repository,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        exp_note_orm = expected_notes_with(id=exp_note_id, amount=1)
        mock_note_repository.get_one_by_id = mock.AsyncMock(return_value=exp_note_orm)

        note = await note_service.get_one_by_id(
            note_id=exp_note_id, md_content_format=md_content_format
        )

        assert note.id == exp_note_id
        assert note.content == (
            markdown.markdown(exp_note_orm.content)
            if not md_content_format
            else exp_note_orm.content
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("md_content_format",), ((True,), (False,)))
    async def test_get_one_by_id_unexisted(
        self,
        md_content_format,
        mock_note_repository,
        note_service,
    ):
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=NoSuchRowError("...")
        )

        with pytest.raises(NoteNotFoundError):
            _ = await note_service.get_one_by_id(
                note_id=uuid.uuid4(), md_content_format=md_content_format
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("title", "content", "owner_id"),
        (
            (
                "Some note title",
                "# Some md content",
                uuid.uuid4(),
            ),
            (
                "Some note title",
                "# Some md content",
                uuid.uuid4(),
            ),
        ),
    )
    async def test_create_one_success(
        self,
        title,
        content,
        owner_id,
        expected_notes_with,
        mock_note_repository,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        exp_note_orm = expected_notes_with(
            title=title, content=content, owner_id=owner_id, amount=1
        )
        expexted_note_sch = NoteCreateShema(
            title=exp_note_orm.title,
            content=exp_note_orm.content,
            owner_id=exp_note_orm.owner_id,
        )

        mock_note_repository.create_one = mock.AsyncMock(return_value=exp_note_id)
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])

        created_note_id = await note_service.create_one(new_note=expexted_note_sch)

        assert created_note_id == exp_note_id
        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.create_one.assert_awaited_once()

        called_note_orm = mock_note_repository.create_one.call_args.kwargs["note"]
        assert called_note_orm.title == exp_note_orm.title
        assert called_note_orm.content == exp_note_orm.content
        assert called_note_orm.owner_id == exp_note_orm.owner_id

    @pytest.mark.asyncio
    async def test_create_one_title_already_exists(
        self,
        expected_notes_with,
        mock_note_repository,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        same_note_title = "Same note title"
        existed_note_with_same_title = expected_notes_with(
            title=same_note_title, amount=1
        )
        expexted_note_sch = NoteCreateShema(
            title=same_note_title,
            content="# SOme md content",
            owner_id=uuid.uuid4(),
        )

        mock_note_repository.create_one = mock.AsyncMock(return_value=exp_note_id)
        mock_note_repository.filter_by = mock.AsyncMock(
            return_value=[existed_note_with_same_title]
        )

        with pytest.raises(NoteAlreadyExistsError):
            _ = await note_service.create_one(new_note=expexted_note_sch)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("title", "content", "owner_id"),
        (
            (
                "updated_title",
                "# Updated md /n/n - item",
                uuid.uuid4(),
            ),
            ("only_title_updated", None, None),
            (None, "# Only content updated", None),
            (None, None, uuid.uuid4()),
        ),
    )
    async def test_update_one_success(
        self,
        title,
        content,
        owner_id,
        mock_note_repository,
        expected_notes_with,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        existed_note_orm_on_update = expected_notes_with(amount=1)
        note_update_schema = NoteUpdateShema(
            title=title, content=content, owner_id=owner_id
        )

        mock_note_repository.get_one_by_id = mock.AsyncMock(
            return_value=existed_note_orm_on_update
        )
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])
        mock_note_repository.update_one = mock.AsyncMock()

        await note_service.update_one(
            note_id=exp_note_id, updated_note=note_update_schema
        )

        mock_note_repository.get_one_by_id.assert_awaited_once_with(note_id=exp_note_id)
        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.update_one.assert_awaited_once()

        called_note = mock_note_repository.update_one.call_args.kwargs["note"]
        assert called_note.title == title
        assert called_note.content == content
        assert called_note.owner_id == owner_id

    @pytest.mark.asyncio
    async def test_update_one_unexists(self, mock_note_repository, note_service):
        exp_note_id = uuid.uuid4()
        note_update_schema = NoteUpdateShema(
            title="some_title",
            content="[content][https://www.some.com]",
            owner_id=uuid.uuid4(),
        )

        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=NoSuchRowError("...")
        )

        with pytest.raises(NoteNotFoundError):
            await note_service.update_one(
                note_id=exp_note_id, updated_note=note_update_schema
            )

            mock_note_repository.get_one_by_id.assert_awaited_once_with(
                note_id=exp_note_id
            )

    @pytest.mark.asyncio
    async def test_update_one_title_already_exists(
        self, expected_notes_with, mock_note_repository, note_service
    ):
        exp_note_id = uuid.uuid4()
        same_note_title = "some_same_title"
        note_orm_on_update = expected_notes_with(title=same_note_title, amount=1)
        existed_note_with_same_title = expected_notes_with(
            title=same_note_title, amount=1
        )
        note_update_schema = NoteUpdateShema(
            title=same_note_title,
            content="### Md content updated",
            owner_id=uuid.uuid4(),
        )

        mock_note_repository.get_one_by_id = mock.AsyncMock(
            return_value=note_orm_on_update
        )
        mock_note_repository.filter_by = mock.AsyncMock(
            return_value=[existed_note_with_same_title]
        )

        with pytest.raises(NoteAlreadyExistsError):
            await note_service.update_one(
                note_id=exp_note_id, updated_note=note_update_schema
            )

            mock_note_repository.get_one_by_id.assert_awaited_once_with(
                note_id=exp_note_id
            )
            mock_note_repository.filter_by.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_one_success(
        self,
        expected_notes_with,
        mock_note_repository,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        exp_note_on_delete = expected_notes_with(id=exp_note_id, amount=1)
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            return_value=exp_note_on_delete
        )
        mock_note_repository.delete_one = mock.AsyncMock()

        await note_service.delete_one(note_id=exp_note_id)

        mock_note_repository.get_one_by_id.assert_awaited_once_with(note_id=exp_note_id)
        mock_note_repository.delete_one.assert_awaited_once()

        called_note = mock_note_repository.delete_one.call_args.kwargs["note"]
        assert called_note == exp_note_on_delete

    @pytest.mark.asyncio
    async def test_delete_one_unexists(
        self,
        mock_note_repository,
        note_service,
    ):
        exp_note_id = uuid.uuid4()
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=NoSuchRowError("...")
        )
        with pytest.raises(NoteNotFoundError):
            await note_service.delete_one(note_id=exp_note_id)

            mock_note_repository.get_one_by_id.assert_awaited_once_with(
                note_id=exp_note_id
            )

    @pytest.mark.asyncio
    async def test_delete_all_by_owner_id(
        self, mock_note_repository, expected_notes_with, note_service
    ):
        note_owner_id = uuid.uuid4()
        exp_notes_on_delete = expected_notes_with(owner_id=note_owner_id, amount=4)
        mock_note_repository.filter_by = mock.AsyncMock(
            return_value=exp_notes_on_delete
        )
        mock_note_repository.delete_all = mock.AsyncMock()

        await note_service.delete_all_by_owner_id(owner_id=note_owner_id)

        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.delete_all.assert_awaited_once()

        called_ids = mock_note_repository.delete_all.call_args.kwargs["note_ids"]
        assert sorted(called_ids) == sorted((note.id for note in exp_notes_on_delete))

    @pytest.mark.asyncio
    async def test_delete_all_by_owner_id_empty(
        self, mock_note_repository, note_service
    ):
        note_owner_id = uuid.uuid4()
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])
        mock_note_repository.delete_all = mock.AsyncMock()

        await note_service.delete_all_by_owner_id(owner_id=note_owner_id)

        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.delete_all.assert_awaited_once()
