from enum import Enum
from datetime import datetime

from sqlalchemy.orm import mapped_column, Mapped 
from sqlalchemy import String, text

from core.database import Base


SQL_TIMEZONE_NOW = text("TIMEZONE('utc', now())")


class Gender(Enum):
    MALE = 'male'
    FEMALE = 'female'
    UNKNOWN = 'unknown'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, 
                                    autoincrement=True)
    username: Mapped[str] = mapped_column(String(50),
                                          unique=True)
    gender: Mapped[Gender] = mapped_column(default=Gender.UNKNOWN)
    age: Mapped[int]

    joined_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW,
        onupdate=SQL_TIMEZONE_NOW
    )