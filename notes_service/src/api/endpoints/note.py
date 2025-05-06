from typing import Annotated

from fastapi import APIRouter, Path, HTTPException, status

from core.database import async_engine
from repositories.note import NoteRepository
from services.note import NoteService
from shemas.note import NoteOutputShema, NoteCreateShema
from exceptions.service import NoteNotFoundError, NoteAlreadyExistsError


notes_router = APIRouter(prefix="/notes")

note_repository = NoteRepository(async_engine)
note_service = NoteService(note_repository)


@notes_router.get("/")
async def get_all() -> list[NoteOutputShema]:
    notes = await note_service.get_all()

    return notes


@notes_router.get("/by-owner-id/{owner_id}")
async def get_all_by_owner_id(
    owner_id: Annotated[int, Path()],
) -> list[NoteOutputShema]:
    notes_by_owner_id = await note_service.get_all_by_owner_id(owner_id=owner_id)

    return notes_by_owner_id


@notes_router.get('/by-id/{note_id}')
async def get_one_by_id(note_id: Annotated[int, Path()]) -> NoteOutputShema:
    try:
        note = await note_service.get_one_by_id(note_id=note_id)
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
