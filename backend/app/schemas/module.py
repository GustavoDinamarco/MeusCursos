# app/schemas/module.py
"""
Schemas Pydantic para Module.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.lesson import LessonResponse


class ModuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Introdução ao Ecossistema"])
    position: int = Field(default=0, ge=0)


class ModuleCreate(ModuleBase):
    """Payload recebido no POST /courses/{id}/modules."""
    pass


class ModuleUpdate(BaseModel):
    """Payload recebido no PATCH /modules/{id} (todos opcionais)."""
    title: str | None = Field(default=None, min_length=1, max_length=255)
    position: int | None = Field(default=None, ge=0)


class ModuleResponse(ModuleBase):
    """Resposta da API — inclui campos gerados pelo banco."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    created_at: datetime


class ModuleWithLessons(ModuleResponse):
    """Resposta detalhada — inclui a lista de aulas do módulo."""
    lessons: list[LessonResponse] = Field(default_factory=list)
