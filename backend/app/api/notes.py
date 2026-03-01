# app/api/notes.py
"""
Rotas de Anotações.

Endpoints:
    POST   /lessons/{lesson_id}/notes          — cria anotação com timestamp
    GET    /lessons/{lesson_id}/notes          — lista anotações da aula
    POST   /lessons/{lesson_id}/export-notion  — exporta anotações para o Notion
    DELETE /notes/{note_id}                    — remove anotação
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.note import NoteCreate, NoteResponse
from app.services import course_service, lesson_service, note_service
from app.services.notion_service import export_notes_to_notion, get_notion_client

# Router aninhado em /lessons (POST e GET de notas por aula)
lessons_router = APIRouter(prefix="/lessons", tags=["notes"])

# Router independente para /notes/{id}
notes_router = APIRouter(prefix="/notes", tags=["notes"])


# ================================================================
# POST /lessons/{lesson_id}/notes — Criar anotação
# ================================================================
@lessons_router.post(
    "/{lesson_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar anotação vinculada a um timestamp do vídeo",
)
async def create_note(
    lesson_id: uuid.UUID,
    data: NoteCreate,
    db: AsyncSession = Depends(get_db),
) -> NoteResponse:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    note = await note_service.create_note(db, lesson_id, data)
    return note  # type: ignore[return-value]


# ================================================================
# GET /lessons/{lesson_id}/notes — Listar anotações da aula
# ================================================================
@lessons_router.get(
    "/{lesson_id}/notes",
    response_model=list[NoteResponse],
    summary="Listar anotações de uma aula ordenadas por timestamp",
)
async def list_notes(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> list[NoteResponse]:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    notes = await note_service.list_notes_by_lesson(db, lesson_id)
    return notes  # type: ignore[return-value]


# ================================================================
# POST /lessons/{lesson_id}/export-notion — Exportar para Notion
# ================================================================
class NotionExportResponse(BaseModel):
    notion_url: str


@lessons_router.post(
    "/{lesson_id}/export-notion",
    response_model=NotionExportResponse,
    summary="Exportar anotações da aula para uma página do Notion",
)
async def export_to_notion(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> NotionExportResponse:
    settings = get_settings()
    if not settings.notion_api_key or not settings.notion_database_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Notion não configurado. Defina NOTION_API_KEY e NOTION_DATABASE_ID.",
        )

    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )

    notes = await note_service.list_notes_by_lesson(db, lesson_id)
    if not notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhuma anotação para exportar.",
        )

    course = await course_service.get_course(db, lesson.course_id)
    course_title = course.title if course else "Curso"

    notion_client = get_notion_client()
    try:
        notion_url = await export_notes_to_notion(
            notion_client, notes, lesson.title, course_title
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro ao exportar para o Notion: {exc}",
        ) from exc

    return NotionExportResponse(notion_url=notion_url)


# ================================================================
# DELETE /notes/{note_id} — Remover anotação
# ================================================================
@notes_router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover uma anotação",
)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    note = await note_service.get_note(db, note_id)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Anotação {note_id} não encontrada.",
        )
    await note_service.delete_note(db, note)
