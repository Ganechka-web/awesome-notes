from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class NoteCreateShema(BaseModel):
    title: str
    content: str
    owner_id: int

    class Config:
        from_attributes = True


class NoteUpdateShema(NoteCreateShema):
    title: Optional[str] = None
    content: Optional[str] = None
    owner_id: Optional[int] = None


class NoteOutputShema(NoteCreateShema):
    id: int
    created_at: datetime
    updated_at: datetime
