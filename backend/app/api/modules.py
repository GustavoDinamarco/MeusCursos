# app/api/modules.py
"""
Rotas de Módulos.

Endpoints:
    POST   /courses/{course_id}/modules  — cria módulo em um curso
    PATCH  /modules/{id}                — atualiza título/posição
    DELETE /modules/{id}                — exclui módulo (aulas ficam sem módulo)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.module import ModuleCreate, ModuleResponse, ModuleUpdate
from app.services import course_service, module_service

# Router aninhado em /courses (POST /courses/{id}/modules)
courses_router = APIRouter(prefix="/courses", tags=["modules"])

# Router independente para rotas /modules/{id}/...
modules_router = APIRouter(prefix="/modules", tags=["modules"])


# ================================================================
# POST /courses/{id}/modules — Criar módulo
# ================================================================
@courses_router.post(
    "/{course_id}/modules",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um módulo no curso",
)
async def create_module(
    course_id: uuid.UUID,
    data: ModuleCreate,
    db: AsyncSession = Depends(get_db),
) -> ModuleResponse:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )
    module = await module_service.create_module(db, course_id, data)
    return module  # type: ignore[return-value]


# ================================================================
# PATCH /modules/{id} — Atualizar módulo
# ================================================================
@modules_router.patch(
    "/{module_id}",
    response_model=ModuleResponse,
    summary="Atualizar título e/ou posição de um módulo",
)
async def update_module(
    module_id: uuid.UUID,
    data: ModuleUpdate,
    db: AsyncSession = Depends(get_db),
) -> ModuleResponse:
    module = await module_service.get_module(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Módulo {module_id} não encontrado.",
        )
    module = await module_service.update_module(db, module, data)
    return module  # type: ignore[return-value]


# ================================================================
# DELETE /modules/{id} — Excluir módulo
# ================================================================
@modules_router.delete(
    "/{module_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir módulo (aulas ficam sem módulo)",
)
async def delete_module(
    module_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    module = await module_service.get_module(db, module_id)
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Módulo {module_id} não encontrado.",
        )
    await module_service.delete_module(db, module)
