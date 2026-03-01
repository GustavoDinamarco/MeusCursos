# app/models/course.py
"""
Modelo Course — representa um curso na plataforma.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        # Garante que o UUID é gerado no lado do Python, não do banco,
        # para consistência entre SQLite (testes) e PostgreSQL.
        insert_default=uuid.uuid4,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relacionamento: um Course tem muitas Lessons
    # cascade="all, delete-orphan" → ao deletar curso, deleta as aulas
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relacionamento: um Course tem muitos Modules
    modules: Mapped[list["Module"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Course id={self.id!s:.8} title={self.title!r}>"
