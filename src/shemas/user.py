from datetime import datetime

from pydantic import BaseModel, Field


class UserCreateShema(BaseModel):
    username: str = Field(max_length=50)
    gender: str
    age: int

    class Config:
        from_attributes = True


class UserUpgrateShema(UserCreateShema):
    pass


class UserOutputShema(UserCreateShema):
    id: int
    joined_at: datetime
    updated_at: datetime


class UserShema(UserOutputShema):
    password: str
