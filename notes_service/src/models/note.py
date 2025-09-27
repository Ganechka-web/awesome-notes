from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, text, UUID as SQL_UUID

from src.core.database import Base


SQL_TIMEZONE_NOW = text("TIMEZONE('utc', now())")


class Note(Base):
    __tablename__ = 'notes'

    id: Mapped[UUID] = mapped_column(SQL_UUID, primary_key=True, default=uuid4)
    title: Mapped[str]
    # content field contains note`s in MarkDown format
    content: Mapped[str] = mapped_column(Text) 
    created_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW
    )
    # This field is for relation with users table 
    owner_id: Mapped[UUID] = mapped_column(SQL_UUID, index=True)
