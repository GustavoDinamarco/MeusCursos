# app/schemas/note.py
"""
Schemas Pydantic para Note.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteBase(BaseModel):
    content: str = Field(..., min_length=1, examples=["Conceito importante sobre async/await"])
    video_timestamp: int = Field(
        ...,
        ge=0,
        description="Posição do vídeo em segundos inteiros",
        examples=[125],
    )


class NoteCreate(NoteBase):
    """Payload recebido no POST /lessons/{id}/notes."""
    pass


class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lesson_id: uuid.UUID
    created_at: datetime
