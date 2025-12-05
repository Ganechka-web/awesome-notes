from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import String, text, SmallInteger
from sqlalchemy import UUID as SQL_UUID

from src.core.database import Base


SQL_TIMEZONE_NOW = text("TIMEZONE('utc', now())")


class Gender(Enum):
    male = "male"
    female = "female"
    unknown = "unknown"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(SQL_UUID, primary_key=True, default=uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    gender: Mapped[Gender] = mapped_column(default=Gender.unknown)
    age: Mapped[int] = mapped_column(SmallInteger)

    joined_at: Mapped[datetime] = mapped_column(server_default=SQL_TIMEZONE_NOW)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW, onupdate=SQL_TIMEZONE_NOW
    )
