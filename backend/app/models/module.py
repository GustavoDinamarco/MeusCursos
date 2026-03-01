# app/models/module.py
"""
Modelo Module — representa um módulo (agrupamento de aulas) dentro de um Course.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        insert_default=uuid.uuid4,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )

    # Relacionamentos
    course: Mapped["Course"] = relationship(  # noqa: F821
        back_populates="modules",
    )
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        back_populates="module",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Module id={self.id!s:.8} title={self.title!r}>"
