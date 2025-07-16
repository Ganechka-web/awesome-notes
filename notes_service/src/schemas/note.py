from typing import Optional
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel


class NoteCreateShema(BaseModel):
    title: str
    content: str
    owner_id: UUID

    class Config:
        from_attributes = True


class NoteUpdateShema(NoteCreateShema):
    title: Optional[str] = None
    content: Optional[str] = None
    owner_id: Optional[UUID] = None


class NoteOutputShema(NoteCreateShema):
    id: UUID
    created_at: datetime
    updated_at: datetime
