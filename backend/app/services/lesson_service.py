# app/services/lesson_service.py
"""
Serviço de Aulas — lógica de negócio relativa a Lesson.
Upload de vídeo e streaming serão adicionados no Passo 4.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson import Lesson
from app.schemas.lesson import LessonCreate, LessonUpdate


async def get_lesson(db: AsyncSession, lesson_id: uuid.UUID) -> Lesson | None:
    """Retorna uma aula pelo ID, incluindo as notas vinculadas."""
    result = await db.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    return result.scalar_one_or_none()


async def create_lesson(
    db: AsyncSession,
    course_id: uuid.UUID,
    data: LessonCreate,
) -> Lesson:
    """Cria uma aula vinculada ao curso informado."""
    lesson = Lesson(
        course_id=course_id,
        title=data.title,
        description=data.description,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def update_lesson(
    db: AsyncSession,
    lesson: Lesson,
    data: LessonUpdate,
) -> Lesson:
    """Atualiza parcialmente uma aula (apenas campos fornecidos)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(lesson, field, value)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def delete_lesson(db: AsyncSession, lesson: Lesson) -> None:
    """Remove a aula e suas notas em cascata."""
    await db.delete(lesson)
    await db.commit()


async def complete_lesson(db: AsyncSession, lesson: Lesson) -> Lesson:
    """Marca a aula como concluída."""
    lesson.completed = True
    lesson.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(lesson)
    return lesson


async def uncomplete_lesson(db: AsyncSession, lesson: Lesson) -> Lesson:
    """Desmarca a aula como concluída."""
    lesson.completed = False
    lesson.completed_at = None
    await db.commit()
    await db.refresh(lesson)
    return lesson
