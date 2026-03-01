# app/services/note_service.py
"""
Serviço de Anotações — lógica de negócio relativa a Note.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.note import Note
from app.schemas.note import NoteCreate


async def list_notes_by_lesson(
    db: AsyncSession,
    lesson_id: uuid.UUID,
) -> list[Note]:
    """Retorna todas as notas de uma aula, ordenadas por timestamp do vídeo."""
    result = await db.execute(
        select(Note)
        .where(Note.lesson_id == lesson_id)
        .order_by(Note.video_timestamp.asc())
    )
    return list(result.scalars().all())


async def get_note(db: AsyncSession, note_id: uuid.UUID) -> Note | None:
    """Retorna uma nota pelo ID."""
    result = await db.execute(select(Note).where(Note.id == note_id))
    return result.scalar_one_or_none()


async def create_note(
    db: AsyncSession,
    lesson_id: uuid.UUID,
    data: NoteCreate,
) -> Note:
    """Cria uma anotação vinculada à aula informada."""
    note = Note(
        lesson_id=lesson_id,
        content=data.content,
        video_timestamp=data.video_timestamp,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


async def delete_note(db: AsyncSession, note: Note) -> None:
    """Remove uma anotação."""
    await db.delete(note)
    await db.commit()
