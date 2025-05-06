from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, text

from core.database import Base


SQL_TIMEZONE_NOW = text("TIMEZONE('utc', now())")


class Note(Base):
    __tablename__ = 'notes'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text) 
    created_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=SQL_TIMEZONE_NOW
    )
    # This field is for relation with users table 
    owner_id: Mapped[int] = mapped_column(index=True)
