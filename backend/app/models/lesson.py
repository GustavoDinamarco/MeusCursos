# app/models/lesson.py
"""
Modelo Lesson — representa uma aula dentro de um Course.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        insert_default=uuid.uuid4,
    )
    # FK para Course — ON DELETE CASCADE garante integridade no banco
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Caminho do objeto no MinIO, ex: "course-videos/uuid/video.mp4"
    video_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Módulo ao qual a aula pertence (opcional)
    module_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("modules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relacionamentos
    course: Mapped["Course"] = relationship(  # noqa: F821
        back_populates="lessons",
    )
    module: Mapped["Module | None"] = relationship(  # noqa: F821
        back_populates="lessons",
    )
    notes: Mapped[list["Note"]] = relationship(  # noqa: F821
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Lesson id={self.id!s:.8} title={self.title!r}>"
