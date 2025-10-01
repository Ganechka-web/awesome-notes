import uuid
from unittest import mock
from contextlib import nullcontext as does_not_raise

import markdown
import pytest

from src.exceptions.service import NoteNotFoundError, NoteAlreadyExistsError
from src.exceptions.repository import NoSuchRowError
from src.schemas.note import NoteCreateShema, NoteUpdateShema


class TestNoteService:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("md_content_format",), ((True,), (False,)))
    async def test_get_all(
        self, md_content_format, mock_note_repository, note_service, expected_notes_orm
    ):
        mock_note_repository.get_all = mock.AsyncMock(return_value=expected_notes_orm)

        notes = await note_service.get_all(md_content_format=md_content_format)

        for note_schema, note_orm in zip(notes, expected_notes_orm):
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
        mock_note_repository,
        note_service,
        expected_notes_orm_with_same_ids,
    ):
        repo_return_value = expected_notes_orm_with_same_ids(owner_id=owner_id)
        mock_note_repository.filter_by = mock.AsyncMock(return_value=repo_return_value)

        notes_by_owner_id = await note_service.get_all_by_owner_id(
            owner_id=owner_id, md_content_format=md_content_format
        )

        assert all(map(lambda nboi: nboi.owner_id == owner_id, notes_by_owner_id))
        mock_note_repository.filter_by.assert_awaited_once()
        for note_schema, note_orm in zip(notes_by_owner_id, repo_return_value):
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
    @pytest.mark.parametrize(
        ("id", "md_content_format", "raised_exception", "expected_exception"),
        (
            (uuid.uuid4(), True, None, does_not_raise()),
            (uuid.uuid4(), False, None, does_not_raise()),
            (
                uuid.uuid4(),
                True,
                NoSuchRowError("..."),
                pytest.raises(NoteNotFoundError),
            ),
        ),
    )
    async def test_get_one_by_id(
        self,
        id,
        md_content_format,
        raised_exception,
        expected_exception,
        mock_note_repository,
        expected_note_with,
        note_service,
    ):
        repo_return_value = expected_note_with(id=id)
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=raised_exception or [repo_return_value]
        )

        with expected_exception:
            note = await note_service.get_one_by_id(
                note_id=id, md_content_format=md_content_format
            )

            assert note.id == id
            assert note.content == (
                markdown.markdown(repo_return_value.content)
                if not md_content_format
                else repo_return_value.content
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("title", "content", "owner_id", "raised_exception", "expected_exception"),
        (
            (
                "Some note title",
                "# Some md content",
                uuid.uuid4(),
                None,
                does_not_raise(),
            ),
            (
                "Some note title",
                "# Some md content",
                uuid.uuid4(),
                NoteAlreadyExistsError("..."),
                pytest.raises(NoteAlreadyExistsError),
            ),
        ),
    )
    async def test_create_one(
        self,
        title,
        content,
        owner_id,
        raised_exception,
        expected_exception,
        mock_note_repository,
        note_service,
    ):
        repo_retrun_id = uuid.uuid4()
        mock_note_repository.filter_by = mock.AsyncMock(
            side_effect=raised_exception or [[]]
        )
        mock_note_repository.create_one = mock.AsyncMock(return_value=repo_retrun_id)

        with expected_exception:
            note_schema = NoteCreateShema(
                title=title, content=content, owner_id=owner_id
            )
            created_note_id = await note_service.create_one(new_note=note_schema)

            assert created_note_id == repo_retrun_id
            mock_note_repository.filter_by.assert_awaited_once()
            mock_note_repository.create_one.assert_awaited_once()

            called_note_orm = mock_note_repository.create_one.call_args.kwargs["note"]
            assert called_note_orm.title == title
            assert called_note_orm.content == content
            assert called_note_orm.owner_id == owner_id

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
        expected_note_with,
        note_service,
    ):
        note_update_schema = NoteUpdateShema(
            title=title, content=content, owner_id=owner_id
        )
        note_on_update = expected_note_with()
        note_on_update_id = uuid.uuid4()
        mock_note_repository.get_one_by_id = mock.AsyncMock(return_value=note_on_update)
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])
        mock_note_repository.update_one = mock.AsyncMock()

        await note_service.update_one(
            note_id=note_on_update_id, updated_note=note_update_schema
        )

        mock_note_repository.get_one_by_id.assert_awaited_once_with(
            note_id=note_on_update_id
        )
        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.update_one.assert_awaited_once()

        called_note = mock_note_repository.update_one.call_args.kwargs["note"]
        assert called_note.title == note_on_update.title
        assert called_note.content == note_on_update.content
        assert called_note.owner_id == note_on_update.owner_id

    @pytest.mark.asyncio
    async def test_update_one_unexists(
        self, mock_note_repository, expected_note_with, note_service
    ):
        note_on_update = expected_note_with()
        note_update_schema = NoteUpdateShema(
            title=note_on_update.title,
            content=note_on_update.content,
            owner_id=note_on_update.owner_id,
        )
        note_on_update_id = uuid.uuid4()
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=NoSuchRowError("...")
        )

        with pytest.raises(NoteNotFoundError):
            await note_service.update_one(
                note_id=note_on_update_id, updated_note=note_update_schema
            )

            mock_note_repository.get_one_by_id.assert_awaited_once_with(
                note_id=note_on_update_id
            )

    @pytest.mark.asyncio
    async def test_update_one_already_exists(
        self, mock_note_repository, expected_note_with, note_service
    ):
        note_on_update = expected_note_with()
        exist_note = expected_note_with(title=note_on_update.title)
        note_update_schema = NoteUpdateShema(
            title=note_on_update.title,
            content=note_on_update.content,
            owner_id=note_on_update.owner_id,
        )
        note_on_update_id = uuid.uuid4()
        mock_note_repository.get_one_by_id = mock.AsyncMock(return_value=note_on_update)
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[exist_note])

        with pytest.raises(NoteAlreadyExistsError):
            await note_service.update_one(
                note_id=note_on_update_id, updated_note=note_update_schema
            )

            mock_note_repository.get_one_by_id.assert_awaited_once_with(
                note_id=note_on_update_id
            )
            mock_note_repository.filter_by.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("note_id", "raised_exception", "expected_exception"),
        (
            (uuid.uuid4(), None, does_not_raise()),
            (uuid.uuid4(), NoSuchRowError("..."), pytest.raises(NoteNotFoundError)),
        ),
    )
    async def test_delete_one(
        self,
        note_id,
        raised_exception,
        expected_exception,
        mock_note_repository,
        expected_note_with,
        note_service,
    ):
        note_on_delete = expected_note_with(id=note_id)
        mock_note_repository.get_one_by_id = mock.AsyncMock(
            side_effect=raised_exception or [note_on_delete]
        )
        mock_note_repository.delete_one = mock.AsyncMock()

        with expected_exception:
            await note_service.delete_one(note_id=note_id)

            mock_note_repository.get_one_by_id.assert_awaited_once_with(note_id=note_id)
            mock_note_repository.delete_one.assert_awaited_once()

            called_note = mock_note_repository.delete_one.call_args.kwargs["note"]
            assert called_note == note_on_delete

    @pytest.mark.asyncio
    async def test_delete_all_by_owner_id(
        self, mock_note_repository, expected_notes_orm_with_same_ids, note_service
    ):
        owner_id = uuid.uuid4()
        expected_notes_on_delete = expected_notes_orm_with_same_ids(owner_id=owner_id)
        mock_note_repository.filter_by = mock.AsyncMock(
            return_value=expected_notes_on_delete
        )
        mock_note_repository.delete_all = mock.AsyncMock()

        await note_service.delete_all_by_owner_id(owner_id=owner_id)

        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.delete_all.assert_awaited_once()

        called_ids = mock_note_repository.delete_all.call_args.kwargs["note_ids"]
        assert sorted(called_ids) == sorted(
            (note.id for note in expected_notes_on_delete)
        )

    @pytest.mark.asyncio
    async def test_delete_all_by_owner_id_empty(
        self, mock_note_repository, note_service
    ):
        owner_id = uuid.uuid4()
        mock_note_repository.filter_by = mock.AsyncMock(return_value=[])
        mock_note_repository.delete_all = mock.AsyncMock()

        await note_service.delete_all_by_owner_id(owner_id=owner_id)

        mock_note_repository.filter_by.assert_awaited_once()
        mock_note_repository.delete_all.assert_awaited_once()
