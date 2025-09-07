from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, field_serializer

from src.models.user import Gender


class UserCreateShema(BaseModel):
    id: Optional[UUID] = None
    username: str = Field(max_length=50)
    gender: str
    age: int = Field(ge=18, le=110)

    class Config:
        from_attributes = True

    @field_validator("gender")
    @classmethod
    def validate_user_gender(cls, gender: str) -> str:
        genders = (Gender.male.value, Gender.female.value, Gender.unknown.value)
        if gender not in genders:
            raise ValueError(f"Gender can be only {', '.join(genders)}")
        return gender

    @field_serializer("id")
    def serialize_id(self, id: UUID, _info) -> str:
        return str(id)


class UserUpgrateShema(UserCreateShema):
    username: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=18, le=110)


class UserOutputShema(UserCreateShema):
    id: UUID
    joined_at: datetime
    updated_at: datetime


class UserShema(UserOutputShema):
    password: str
