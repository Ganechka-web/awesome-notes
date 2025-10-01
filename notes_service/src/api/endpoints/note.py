from typing import Annotated, TYPE_CHECKING
from uuid import UUID

from fastapi import APIRouter, Path, HTTPException, Depends, status
from dependency_injector.wiring import Provide, inject

from src.schemas.note import NoteOutputShema, NoteCreateShema, NoteUpdateShema
from src.exceptions.service import NoteNotFoundError, NoteAlreadyExistsError
from src.container import Container

if TYPE_CHECKING:
    from src.services.note import NoteService


notes_router = APIRouter()


@notes_router.get("/")
@inject
async def get_all(
    md_content_format: bool = False,
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> list[NoteOutputShema]:
    notes = await note_service.get_all(md_content_format=md_content_format)

    return notes


@notes_router.get("/by-owner-id/{owner_id}")
@inject
async def get_all_by_owner_id(
    owner_id: Annotated[UUID, Path()],
    md_content_format: bool = False,
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> list[NoteOutputShema]:
    notes_by_owner_id = await note_service.get_all_by_owner_id(
        owner_id=owner_id, md_content_format=md_content_format
    )

    return notes_by_owner_id


@notes_router.get("/by-id/{note_id}")
@inject
async def get_one_by_id(
    note_id: Annotated[UUID, Path()],
    md_content_format: bool = False,
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> NoteOutputShema:
    try:
        note = await note_service.get_one_by_id(
            note_id=note_id, md_content_format=md_content_format
        )
    except NoteNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")

    return note


@notes_router.post("/create/", status_code=201)
@inject
async def create_one(
    new_note: NoteCreateShema,
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> UUID:
    try:
        new_note_id = await note_service.create_one(new_note=new_note)
    except NoteAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"User already has got anote with title - {new_note.title}",
        )

    return new_note_id


@notes_router.patch("/update/{note_id}")
@inject
async def update_one(
    note_id: Annotated[UUID, Path()],
    updated_note: NoteUpdateShema,
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> None:
    try:
        await note_service.update_one(note_id=note_id, updated_note=updated_note)
    except NoteNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")
    except NoteAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"User already has got a note with title - {updated_note.title}",
        )


@notes_router.delete("/delete/{note_id}", status_code=204)
@inject
async def delete_one(
    note_id: Annotated[UUID, Path()],
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> None:
    try:
        await note_service.delete_one(note_id=note_id)
    except NoteNotFoundError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Note not found")


@notes_router.delete("/delete/by-owner-id/{owner_id}", status_code=204)
@inject
async def delete_all_by_owner_id(
    owner_id: Annotated[UUID, Path()],
    note_service: "NoteService" = Depends(Provide[Container.note_service]),
) -> None:
    await note_service.delete_all_by_owner_id(owner_id=owner_id)
