from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, field_serializer

from src.models.user import Gender


class ValidateGenderMixin:
    @field_validator("gender")
    @classmethod
    def validate_user_gender(cls, gender: str) -> str:
        genders = (Gender.male.value, Gender.female.value, Gender.unknown.value)
        if gender not in genders and gender is not None:
            raise ValueError(f"Gender can be only {', '.join(genders)}")
        return gender


class SerializeIdMixin:
    @field_serializer("id")
    def serialize_id(self, id: UUID, _info) -> str:
        return str(id)


class UserCreateShema(BaseModel, ValidateGenderMixin):
    username: str = Field(max_length=50)
    gender: str
    age: int = Field(ge=18, le=110)


class UserUpgrateShema(BaseModel, ValidateGenderMixin):
    username: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = None
    age: Optional[int] = Field(default=None, ge=18, le=110)


class UserOutputShema(BaseModel, SerializeIdMixin):
    id: UUID
    username: str
    gender: str
    age: int
    joined_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
