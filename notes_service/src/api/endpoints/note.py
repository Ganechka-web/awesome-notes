from typing import Annotated

from fastapi import APIRouter, Path, HTTPException, status

from core.database import async_engine
from repositories.note import NoteRepository
from services.note import NoteService
from shemas.note import (
    NoteOutputShema, 
    NoteCreateShema,
    NoteUpdateShema
)
from exceptions.service import NoteNotFoundError, NoteAlreadyExistsError


notes_router = APIRouter(prefix="/notes")

note_repository = NoteRepository(async_engine)
note_service = NoteService(note_repository)


@notes_router.get("/")
async def get_all(md_content_format: bool = False) -> list[NoteOutputShema]:
    notes = await note_service.get_all(md_content_format=md_content_format)

    return notes


@notes_router.get("/by-owner-id/{owner_id}")
async def get_all_by_owner_id(
    owner_id: Annotated[int, Path()],
    md_content_format: bool = False
) -> list[NoteOutputShema]:
    notes_by_owner_id = await note_service.get_all_by_owner_id(
        owner_id=owner_id, md_content_format=md_content_format
    )

    return notes_by_owner_id


@notes_router.get('/by-id/{note_id}')
async def get_one_by_id(
    note_id: Annotated[int, Path()],
    md_content_format: bool = False
) -> NoteOutputShema:
    try:
        note = await note_service.get_one_by_id(
            note_id=note_id, md_content_format=md_content_format
        )
    except NoteNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )
    
    return note


@notes_router.post('/create/')
async def create_one(new_note: NoteCreateShema) -> int:
    try:
        new_note_id = await note_service.create_one(new_note=new_note)
    except NoteAlreadyExistsError: 
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f'User already has got a'
                   f'note with title - {new_note.title}'
        )
    
    return new_note_id


@notes_router.patch('/update/{note_id}')
async def update_one(
    note_id: Annotated[int, Path()], updated_note: NoteUpdateShema
):
    try: 
        await note_service.update_one(
            note_id=note_id, updated_note=updated_note
        )
    except NoteNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )
    except NoteAlreadyExistsError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f'User already has got a'
                   f'note with title - {updated_note.title}'
        )
    

@notes_router.delete('/delete/{note_id}')
async def delete_one(note_id: Annotated[int, Path()]):
    try:
        await note_service.delete_one(note_id=note_id)
    except NoteNotFoundError:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='Note not found'
        )


@notes_router.delete('delete/by-owner-id/{owner_id}')
async def delete_all_by_owner_id(
    owner_id: Annotated[int, Path()]
) -> None:
    await note_service.delete_all_by_owner_id(owner_id=owner_id)
    