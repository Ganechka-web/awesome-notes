from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, UUID as SQL_UUID

from src.core.database import Base


class AuthCredentials(Base):
    __tablename__ = "auth_credentials"

    id: Mapped[UUID] = mapped_column(SQL_UUID, primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    password: Mapped[str]
