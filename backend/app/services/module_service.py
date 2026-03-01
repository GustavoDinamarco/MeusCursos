# app/services/module_service.py
"""
Serviço de Módulos — lógica de negócio relativa a Module.
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module
from app.schemas.module import ModuleCreate, ModuleUpdate


async def list_modules_by_course(
    db: AsyncSession,
    course_id: uuid.UUID,
) -> list[Module]:
    """Retorna todos os módulos de um curso, ordenados por posição."""
    result = await db.execute(
        select(Module)
        .where(Module.course_id == course_id)
        .order_by(Module.position.asc())
    )
    return list(result.scalars().all())


async def get_module(db: AsyncSession, module_id: uuid.UUID) -> Module | None:
    """Retorna um módulo pelo ID."""
    result = await db.execute(
        select(Module).where(Module.id == module_id)
    )
    return result.scalar_one_or_none()


async def create_module(
    db: AsyncSession,
    course_id: uuid.UUID,
    data: ModuleCreate,
) -> Module:
    """Cria um módulo vinculado ao curso informado."""
    module = Module(
        course_id=course_id,
        title=data.title,
        position=data.position,
    )
    db.add(module)
    await db.commit()
    await db.refresh(module)
    return module


async def update_module(
    db: AsyncSession,
    module: Module,
    data: ModuleUpdate,
) -> Module:
    """Atualiza parcialmente um módulo (apenas campos fornecidos)."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(module, field, value)
    await db.commit()
    await db.refresh(module)
    return module


async def delete_module(db: AsyncSession, module: Module) -> None:
    """Remove o módulo. Aulas com este module_id ficam com module_id=NULL."""
    await db.delete(module)
    await db.commit()
