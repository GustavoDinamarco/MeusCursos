# app/models/note.py
"""
Modelo Note — anotação vinculada a um timestamp exato de uma Lesson.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        insert_default=uuid.uuid4,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Timestamp em segundos inteiros (ex: 125 = 2min05s do vídeo)
    video_timestamp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relacionamento
    lesson: Mapped["Lesson"] = relationship(  # noqa: F821
        back_populates="notes",
    )

    def __repr__(self) -> str:
        return (
            f"<Note id={self.id!s:.8}"
            f" lesson={self.lesson_id!s:.8}"
            f" ts={self.video_timestamp}s>"
        )
