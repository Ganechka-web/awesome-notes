from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreateShema(BaseModel):
    username: str = Field(max_length=50)
    gender: str
    age: int

    class Config:
        from_attributes = True


class UserUpgrateShema(UserCreateShema):
    username: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = None
    age: Optional[int] = None


class UserOutputShema(UserCreateShema):
    id: int
    joined_at: datetime
    updated_at: datetime


class UserShema(UserOutputShema):
    password: str
