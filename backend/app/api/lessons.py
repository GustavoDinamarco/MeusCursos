# app/api/lessons.py
"""
Rotas de Aulas.

Endpoints:
    POST   /courses/{course_id}/lessons       — adiciona aula a um curso
    GET    /lessons/{id}                      — detalhes de uma aula
    PATCH  /lessons/{id}                      — atualiza título/descrição
    DELETE /lessons/{id}                      — exclui a aula (e vídeo MinIO)
    POST   /lessons/{id}/upload-video         — upload de vídeo para o MinIO
    GET    /lessons/{id}/video                — stream do vídeo (com suporte a Range)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.services import course_service, lesson_service
from app.services.minio_service import (
    delete_video,
    get_s3_client,
    get_video_metadata,
    stream_video,
    upload_video,
    validate_video_extension,
)

# Router de lições aninhadas em /courses (POST /courses/{id}/lessons)
courses_router = APIRouter(prefix="/courses", tags=["lessons"])

# Router independente para rotas /lessons/{id}/...
lessons_router = APIRouter(prefix="/lessons", tags=["lessons"])


# ================================================================
# POST /courses/{id}/lessons — Criar aula
# ================================================================
@courses_router.post(
    "/{course_id}/lessons",
    response_model=LessonResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar uma aula ao curso",
)
async def create_lesson(
    course_id: uuid.UUID,
    data: LessonCreate,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )
    lesson = await lesson_service.create_lesson(db, course_id, data)
    return lesson  # type: ignore[return-value]


# ================================================================
# GET /lessons/{id} — Detalhes da aula
# ================================================================
@lessons_router.get(
    "/{lesson_id}",
    response_model=LessonResponse,
    summary="Detalhes de uma aula",
)
async def get_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    return lesson  # type: ignore[return-value]


# ================================================================
# PATCH /lessons/{id} — Atualizar título/descrição
# ================================================================
@lessons_router.patch(
    "/{lesson_id}",
    response_model=LessonResponse,
    summary="Atualizar título e/ou descrição de uma aula",
)
async def update_lesson(
    lesson_id: uuid.UUID,
    data: LessonUpdate,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    lesson = await lesson_service.update_lesson(db, lesson, data)
    return lesson  # type: ignore[return-value]


# ================================================================
# DELETE /lessons/{id} — Excluir aula
# ================================================================
@lessons_router.delete(
    "/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir uma aula (e seu vídeo no MinIO, se houver)",
)
async def delete_lesson(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    # Remove o vídeo do MinIO se existir (drive/youtube não têm arquivo local)
    if lesson.video_url and not lesson.video_url.startswith(("drive:", "youtube:")):
        settings = get_settings()
        s3 = get_s3_client()
        await delete_video(s3, settings.minio_bucket_name, lesson.video_url)
    await lesson_service.delete_lesson(db, lesson)


# ================================================================
# POST /lessons/{id}/upload-video — Upload de vídeo para o MinIO
# ================================================================
@lessons_router.post(
    "/{lesson_id}/upload-video",
    response_model=LessonResponse,
    summary="Upload do arquivo de vídeo para o MinIO",
)
async def upload_lesson_video(
    lesson_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    # 1. Verifica se a aula existe
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )

    # 2. Valida extensão do arquivo
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome do arquivo é obrigatório.",
        )
    try:
        ext, content_type = validate_video_extension(file.filename)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    # 3. Se já existe um vídeo anterior no MinIO, remove do MinIO
    settings = get_settings()
    s3 = get_s3_client()
    if lesson.video_url and not lesson.video_url.startswith(("drive:", "youtube:")):
        await delete_video(s3, settings.minio_bucket_name, lesson.video_url)

    # 4. Upload para o MinIO
    object_key = await upload_video(
        s3_client=s3,
        bucket=settings.minio_bucket_name,
        file=file.file,
        lesson_id=lesson_id,
        ext=ext,
        content_type=content_type,
    )

    # 5. Atualiza o video_url da aula no banco
    lesson.video_url = object_key
    await db.commit()
    await db.refresh(lesson)

    return lesson  # type: ignore[return-value]


# ================================================================
# GET /lessons/{id}/video — Stream do vídeo com suporte a Range
# ================================================================
@lessons_router.get(
    "/{lesson_id}/video",
    summary="Stream do vídeo do MinIO (suporta Range para seeking)",
)
async def stream_lesson_video(
    lesson_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    # 1. Verifica se a aula existe e tem vídeo
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    if not lesson.video_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Esta aula não possui vídeo.",
        )
    # Vídeos externos (Drive/YouTube) não são streamados pelo servidor
    if lesson.video_url.startswith(("drive:", "youtube:")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vídeo externo — reproduzido diretamente no navegador via embed.",
        )

    settings = get_settings()
    s3 = get_s3_client()

    # 2. Captura o header Range (ex: "bytes=0-1048576")
    range_header = request.headers.get("range")

    # 3. Obtém o stream e os metadados do MinIO
    stream, metadata = await stream_video(
        s3_client=s3,
        bucket=settings.minio_bucket_name,
        object_key=lesson.video_url,
        range_header=range_header,
    )

    # 4. Monta a resposta com headers apropriados
    response_headers: dict[str, str] = {
        "Accept-Ranges": metadata["AcceptRanges"],
        "Content-Length": str(metadata["ContentLength"]),
    }

    # Se há Range, retorna 206 Partial Content
    if range_header and metadata.get("ContentRange"):
        response_headers["Content-Range"] = metadata["ContentRange"]
        return StreamingResponse(
            content=stream,
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            media_type=metadata["ContentType"],
            headers=response_headers,
        )

    # Sem Range → 200 completo
    return StreamingResponse(
        content=stream,
        status_code=status.HTTP_200_OK,
        media_type=metadata["ContentType"],
        headers=response_headers,
    )


# ================================================================
# POST /lessons/{id}/complete — Marcar aula como concluída
# ================================================================
@lessons_router.post(
    "/{lesson_id}/complete",
    response_model=LessonResponse,
    summary="Marcar aula como concluída",
)
async def mark_lesson_complete(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    lesson = await lesson_service.complete_lesson(db, lesson)
    return lesson  # type: ignore[return-value]


# ================================================================
# DELETE /lessons/{id}/complete — Desmarcar aula como concluída
# ================================================================
@lessons_router.delete(
    "/{lesson_id}/complete",
    response_model=LessonResponse,
    summary="Desmarcar aula como concluída",
)
async def unmark_lesson_complete(
    lesson_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    lesson = await lesson_service.get_lesson(db, lesson_id)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aula {lesson_id} não encontrada.",
        )
    lesson = await lesson_service.uncomplete_lesson(db, lesson)
    return lesson  # type: ignore[return-value]
