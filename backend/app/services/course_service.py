# app/services/course_service.py
"""
Serviço de Cursos — contém toda a lógica de negócio relativa a Course.
As funções recebem uma AsyncSession e retornam entidades ORM ou None.
A camada de API é responsável por transformar None em HTTPException.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.schemas.course import CourseCreate, CourseUpdate


async def list_courses(db: AsyncSession) -> list[Course]:
    """Retorna todos os cursos ordenados do mais recente para o mais antigo."""
    result = await db.execute(
        select(Course).order_by(Course.created_at.desc())
    )
    return list(result.scalars().all())


async def get_course(db: AsyncSession, course_id: uuid.UUID) -> Course | None:
    """Retorna um curso pelo ID, incluindo as aulas (selectin já carrega)."""
    result = await db.execute(
        select(Course).where(Course.id == course_id)
    )
    return result.scalar_one_or_none()


async def create_course(db: AsyncSession, data: CourseCreate) -> Course:
    """Persiste um novo curso e retorna a entidade com o ID gerado."""
    course = Course(title=data.title, description=data.description)
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def update_course(
    db: AsyncSession,
    course: Course,
    data: CourseUpdate,
) -> Course:
    """
    Atualiza apenas os campos fornecidos (partial update).
    Recebe a entidade já buscada para evitar dupla consulta.
    """
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(course, field, value)
    await db.commit()
    await db.refresh(course)
    return course


async def delete_course(db: AsyncSession, course: Course) -> None:
    """Remove o curso e suas aulas em cascata."""
    await db.delete(course)
    await db.commit()
