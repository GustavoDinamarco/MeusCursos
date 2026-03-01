# app/schemas/lesson.py
"""
Schemas Pydantic para Lesson.
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


class LessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, examples=["Introdução ao FastAPI"])
    description: str | None = Field(default=None)


class LessonCreate(LessonBase):
    """Payload recebido no POST /courses/{id}/lessons."""
    pass


class LessonUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    module_id: uuid.UUID | None = None
    position: int | None = Field(default=None, ge=0)


class LessonResponse(LessonBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    video_url: str | None
    module_id: uuid.UUID | None = None
    position: int = 0
    completed: bool = False
    completed_at: datetime | None = None
    created_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def video_source(self) -> Literal["minio", "google_drive", "youtube"] | None:
        """Derivado do prefixo de video_url. Sem migração de banco necessária."""
        if not self.video_url:
            return None
        if self.video_url.startswith("drive:"):
            return "google_drive"
        if self.video_url.startswith("youtube:"):
            return "youtube"
        return "minio"
