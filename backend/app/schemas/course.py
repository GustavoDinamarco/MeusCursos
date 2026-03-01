# app/schemas/course.py
"""
Schemas Pydantic para Course.
Padrão: Base → Create (entrada) → Response (saída com id/timestamps).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Não há import circular: lesson.py não importa course.py
from app.schemas.lesson import LessonResponse
from app.schemas.module import ModuleWithLessons


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Python para Engenheiros"])
    description: str | None = Field(default=None, examples=["Curso completo de Python"])
    thumbnail_url: str | None = Field(default=None, max_length=512)


class CourseCreate(CourseBase):
    """Payload recebido no POST /courses."""
    pass


class CourseUpdate(BaseModel):
    """Payload recebido no PATCH /courses/{id} (todos opcionais)."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    thumbnail_url: str | None = None


class CourseResponse(CourseBase):
    """Resposta da API — inclui campos gerados pelo banco."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class CourseWithLessons(CourseResponse):
    """
    Resposta detalhada do GET /courses/{id}.
    Inclui a lista completa de aulas e módulos do curso.
    """
    lessons: list[LessonResponse] = Field(default_factory=list)
    modules: list[ModuleWithLessons] = Field(default_factory=list)
