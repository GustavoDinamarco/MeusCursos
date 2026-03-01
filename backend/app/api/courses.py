# app/api/courses.py
"""
Rotas de Cursos.

Endpoints implementados:
    GET    /courses                        — lista cursos
    POST   /courses                        — cria curso
    GET    /courses/{id}                   — detalhe do curso com aulas
    DELETE /courses/{id}                   — remove curso (cascade para aulas/notas)
    POST   /courses/{id}/upload-thumbnail  — upload de thumbnail (imagem)
    GET    /courses/{id}/thumbnail         — serve a thumbnail
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.course import CourseCreate, CourseResponse, CourseWithLessons
from app.services import course_service
from app.services.minio_service import (
    delete_video,
    get_s3_client,
    get_video_metadata,
    stream_video,
    upload_image,
    validate_image_extension,
)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get(
    "",
    response_model=list[CourseWithLessons],
    summary="Listar todos os cursos (com aulas e módulos)",
)
async def list_courses(
    db: AsyncSession = Depends(get_db),
) -> list[CourseWithLessons]:
    courses = await course_service.list_courses(db)
    return courses  # type: ignore[return-value]


@router.post(
    "",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar um novo curso",
)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await course_service.create_course(db, data)
    return course  # type: ignore[return-value]


@router.get(
    "/{course_id}",
    response_model=CourseWithLessons,
    summary="Detalhes do curso com suas aulas",
)
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CourseWithLessons:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )
    return course  # type: ignore[return-value]


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover curso e todas as suas aulas/notas",
)
async def delete_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )
    await course_service.delete_course(db, course)


@router.post(
    "/{course_id}/upload-thumbnail",
    response_model=CourseResponse,
    summary="Upload de thumbnail para o curso",
)
async def upload_course_thumbnail(
    course_id: uuid.UUID,
    file: UploadFile,
    db: AsyncSession = Depends(get_db),
) -> CourseResponse:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )

    try:
        ext, content_type = validate_image_extension(file.filename or "image.jpg")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    settings = get_settings()
    s3 = get_s3_client()

    # Remove thumbnail anterior do MinIO (se for object key, não URL externa)
    if course.thumbnail_url and not course.thumbnail_url.startswith("http"):
        await delete_video(s3, settings.minio_bucket_name, course.thumbnail_url)

    object_key = await upload_image(
        s3, settings.minio_bucket_name, file.file, "thumbnails", ext, content_type
    )
    course.thumbnail_url = object_key
    await db.commit()
    await db.refresh(course)
    return course  # type: ignore[return-value]


@router.get(
    "/{course_id}/thumbnail",
    summary="Serve a thumbnail do curso",
)
async def get_course_thumbnail(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )

    if not course.thumbnail_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curso não possui thumbnail.",
        )

    # URL externa → redirect
    if course.thumbnail_url.startswith("http"):
        return RedirectResponse(course.thumbnail_url)  # type: ignore[return-value]

    # Object key no MinIO → stream
    settings = get_settings()
    s3 = get_s3_client()

    try:
        meta = await get_video_metadata(s3, settings.minio_bucket_name, course.thumbnail_url)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail não encontrada no storage.",
        )

    stream, _ = await stream_video(s3, settings.minio_bucket_name, course.thumbnail_url)
    return StreamingResponse(
        stream,
        media_type=meta.get("ContentType", "image/jpeg"),
        headers={"Content-Length": str(meta["ContentLength"])},
    )
