from enum import Enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import mapped_column, Mapped
from sqlalchemy import FetchedValue, String, SmallInteger, DateTime
from sqlalchemy import UUID as SQL_UUID

from src.core.database import Base


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

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), server_default=FetchedValue()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
    )
