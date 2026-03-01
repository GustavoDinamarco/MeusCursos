# app/api/imports.py
"""
Endpoints de importação em lote a partir de fontes externas.

Endpoints:
    POST /courses/{course_id}/import-drive   — importa vídeos de uma pasta do Google Drive
    POST /courses/{course_id}/import-youtube — importa vídeos de uma playlist do YouTube
    GET  /imports/local/browse               — lista arquivos da pasta local de imports
    POST /courses/{course_id}/import-local   — importa vídeos de uma pasta local (stream NDJSON)
"""
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.database import AsyncSessionLocal, get_db
from app.models.lesson import Lesson
from app.schemas.lesson import LessonResponse
from app.services import course_service, minio_service
from app.services.google_drive_service import list_folder_videos, parse_folder_id
from app.services.local_import_service import (
    check_imports_available,
    filename_to_title,
    list_entries,
    list_video_files,
    validate_path,
)
from app.services.minio_service import get_s3_client, validate_video_extension
from app.services.youtube_service import list_playlist_videos

router = APIRouter(prefix="/courses", tags=["imports"])
local_router = APIRouter(prefix="/imports", tags=["imports"])


# ----------------------------------------------------------------
# Schemas de request / response
# ----------------------------------------------------------------

class DriveImportPayload(BaseModel):
    folder_url: str


class YoutubeImportPayload(BaseModel):
    playlist_url: str


class LocalImportPayload(BaseModel):
    folder_path: str = ""
    module_id: uuid.UUID | None = None


class ImportResult(BaseModel):
    imported: int
    lessons: list[LessonResponse]


class LocalBrowseEntry(BaseModel):
    name: str
    type: str  # "directory" | "file"
    size_bytes: int | None = None
    path: str


class LocalBrowseResponse(BaseModel):
    available: bool
    path: str
    entries: list[LocalBrowseEntry]


# ----------------------------------------------------------------
# Helper interno
# ----------------------------------------------------------------

async def _create_lessons_batch(
    db: AsyncSession,
    course_id: uuid.UUID,
    items: list[dict],  # [{title, video_url}]
) -> list[Lesson]:
    """Cria todas as aulas em um único commit."""
    lessons: list[Lesson] = []
    for item in items:
        lesson = Lesson(
            course_id=course_id,
            title=item["title"],
            video_url=item["video_url"],
        )
        db.add(lesson)
        lessons.append(lesson)

    await db.commit()
    for lesson in lessons:
        await db.refresh(lesson)
    return lessons


def _require_api_key(settings: Settings) -> str:
    """Retorna a chave de API do Google ou levanta 503."""
    if not settings.google_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Chave do Google API não configurada. "
                "Defina GOOGLE_API_KEY no arquivo .env."
            ),
        )
    return settings.google_api_key


# ================================================================
# POST /courses/{id}/import-drive
# ================================================================

@router.post(
    "/{course_id}/import-drive",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Importar vídeos de uma pasta pública do Google Drive",
)
async def import_from_drive(
    course_id: uuid.UUID,
    data: DriveImportPayload,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> ImportResult:
    # 1. Curso deve existir
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )

    # 2. API key obrigatória
    api_key = _require_api_key(settings)

    # 3. Parseia o folder ID
    try:
        folder_id = parse_folder_id(data.folder_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    # 4. Lista os vídeos da pasta
    try:
        videos = await list_folder_videos(folder_id, api_key)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    if not videos:
        return ImportResult(imported=0, lessons=[])

    # 5. Cria as aulas
    items = [
        {"title": v["name"], "video_url": f"drive:{v['id']}"}
        for v in videos
    ]
    lessons = await _create_lessons_batch(db, course_id, items)

    return ImportResult(
        imported=len(lessons),
        lessons=[LessonResponse.model_validate(lesson) for lesson in lessons],
    )


# ================================================================
# POST /courses/{id}/import-youtube
# ================================================================

@router.post(
    "/{course_id}/import-youtube",
    response_model=ImportResult,
    status_code=status.HTTP_201_CREATED,
    summary="Importar vídeos de uma playlist pública do YouTube",
)
async def import_from_youtube(
    course_id: uuid.UUID,
    data: YoutubeImportPayload,
    db: AsyncSession = Depends(get_db),
) -> ImportResult:
    # 1. Curso deve existir
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )

    # 2. Lista os vídeos da playlist (sem API key — usa yt-dlp)
    try:
        videos = await list_playlist_videos(data.playlist_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )

    if not videos:
        return ImportResult(imported=0, lessons=[])

    # 3. Cria as aulas
    items = [
        {"title": v["title"], "video_url": f"youtube:{v['videoId']}"}
        for v in videos
    ]
    lessons = await _create_lessons_batch(db, course_id, items)

    # 4. Auto-set thumbnail do YouTube (primeiro vídeo da playlist)
    if not course.thumbnail_url and videos:
        first_id = videos[0]["videoId"]
        course.thumbnail_url = f"https://img.youtube.com/vi/{first_id}/hqdefault.jpg"
        await db.commit()
        await db.refresh(course)

    return ImportResult(
        imported=len(lessons),
        lessons=[LessonResponse.model_validate(lesson) for lesson in lessons],
    )


# ================================================================
# GET /imports/local/browse
# ================================================================

@local_router.get(
    "/local/browse",
    response_model=LocalBrowseResponse,
    summary="Listar arquivos e pastas do diretório local de imports",
)
async def browse_local(
    path: str = Query(default="", description="Subcaminho relativo"),
) -> LocalBrowseResponse:
    if not check_imports_available():
        return LocalBrowseResponse(available=False, path=path, entries=[])

    try:
        entries = await list_entries(path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return LocalBrowseResponse(
        available=True,
        path=path,
        entries=[LocalBrowseEntry(**e) for e in entries],
    )


# ================================================================
# POST /courses/{id}/import-local  (Streaming NDJSON)
# ================================================================

@router.post(
    "/{course_id}/import-local",
    summary="Importar vídeos de uma pasta local para o MinIO (stream NDJSON)",
)
async def import_from_local(
    course_id: uuid.UUID,
    data: LocalImportPayload,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Validações síncronas antes de iniciar o stream
    course = await course_service.get_course(db, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Curso {course_id} não encontrado.",
        )

    if not check_imports_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pasta de imports não disponível. Verifique o volume Docker.",
        )

    try:
        video_files = await list_video_files(data.folder_path)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if not video_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum arquivo de vídeo encontrado na pasta.",
        )

    # Captura valores necessários no generator
    total = len(video_files)
    bucket = settings.minio_bucket_name
    module_id = data.module_id

    async def _stream():
        s3 = get_s3_client()
        imported = 0
        created_lessons: list[Lesson] = []

        async with AsyncSessionLocal() as session:
            for idx, vf in enumerate(video_files, start=1):
                filename = vf["name"]
                file_path = validate_path(vf["path"])

                try:
                    ext, content_type = validate_video_extension(filename)
                except ValueError as exc:
                    yield json.dumps({
                        "type": "error",
                        "current": idx,
                        "total": total,
                        "filename": filename,
                        "detail": str(exc),
                    }) + "\n"
                    continue

                # Criar lesson no DB
                title = filename_to_title(filename)
                lesson = Lesson(
                    course_id=course_id,
                    title=title,
                    module_id=module_id,
                )
                session.add(lesson)
                await session.flush()  # Gera o ID

                # Progresso: uploading
                yield json.dumps({
                    "type": "progress",
                    "current": idx,
                    "total": total,
                    "filename": filename,
                    "status": "uploading",
                }) + "\n"

                # Upload para MinIO
                try:
                    with open(file_path, "rb") as f:
                        object_key = await minio_service.upload_video(
                            s3, bucket, f, lesson.id, ext, content_type,
                        )
                    lesson.video_url = object_key
                    imported += 1
                    created_lessons.append(lesson)
                except Exception as exc:
                    yield json.dumps({
                        "type": "error",
                        "current": idx,
                        "total": total,
                        "filename": filename,
                        "detail": f"Erro no upload: {exc}",
                    }) + "\n"
                    await session.delete(lesson)
                    continue

            # Commit de todas as lessons criadas
            await session.commit()
            for lesson in created_lessons:
                await session.refresh(lesson)

            yield json.dumps({
                "type": "result",
                "imported": imported,
                "lessons": [
                    LessonResponse.model_validate(l).model_dump(mode="json")
                    for l in created_lessons
                ],
            }) + "\n"

    return StreamingResponse(
        _stream(),
        media_type="application/x-ndjson",
    )
