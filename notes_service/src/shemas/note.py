from typing import Optional
from datetime import datetime

from pydantic import BaseModel


class NoteCreateShema(BaseModel):
    title: str
    content: str
    owner_id: int


class NoteUpdateShema(NoteCreateShema):
    title: Optional[str]
    content: Optional[str]


class NoteOutputShema(NoteCreateShema):
    id: int
    created_at: datetime
    updated_at: datetime
