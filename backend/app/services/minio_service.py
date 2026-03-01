# app/services/minio_service.py
"""
Serviço de Object Storage — abstrai operações de upload, download e remoção
de vídeos no MinIO (compatível com S3).

Usa boto3 síncrono com asyncio.to_thread() para não bloquear o event loop.
"""
import asyncio
import uuid
from collections.abc import AsyncGenerator
from pathlib import PurePosixPath
from typing import IO, Any

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from app.core.config import get_settings

# Extensões e MIME types de vídeo aceitos
ALLOWED_EXTENSIONS: dict[str, str] = {
    ".mp4": "video/mp4",
    ".mkv": "video/x-matroska",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".m4v": "video/mp4",
}

# Extensões e MIME types de imagem aceitos
ALLOWED_IMAGE_EXTENSIONS: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}

# Tamanho do chunk para streaming (1 MB)
STREAM_CHUNK_SIZE = 1024 * 1024


def get_s3_client() -> Any:
    """
    Cria e retorna um cliente boto3 S3 configurado para o MinIO.
    Chamado como dependency injection no FastAPI.
    """
    settings = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",  # MinIO ignora, mas boto3 exige
    )


def validate_video_extension(filename: str) -> tuple[str, str]:
    """
    Valida a extensão do arquivo e retorna (extensão, content_type).
    Levanta ValueError se a extensão não for permitida.
    """
    ext = PurePosixPath(filename).suffix.lower()
    content_type = ALLOWED_EXTENSIONS.get(ext)
    if content_type is None:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS.keys()))
        raise ValueError(
            f"Extensão '{ext}' não permitida. Use: {allowed}"
        )
    return ext, content_type


def validate_image_extension(filename: str) -> tuple[str, str]:
    """
    Valida a extensão de imagem e retorna (extensão, content_type).
    Levanta ValueError se a extensão não for permitida.
    """
    ext = PurePosixPath(filename).suffix.lower()
    content_type = ALLOWED_IMAGE_EXTENSIONS.get(ext)
    if content_type is None:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS.keys()))
        raise ValueError(
            f"Extensão '{ext}' não permitida para imagem. Use: {allowed}"
        )
    return ext, content_type


def _build_object_key(lesson_id: uuid.UUID, ext: str) -> str:
    """Gera o caminho do objeto no bucket: lessons/{lesson_id}/{uuid}.{ext}"""
    return f"lessons/{lesson_id}/{uuid.uuid4()}{ext}"


async def upload_video(
    s3_client: Any,
    bucket: str,
    file: IO[bytes],
    lesson_id: uuid.UUID,
    ext: str,
    content_type: str,
) -> str:
    """
    Faz upload do vídeo para o MinIO via streaming (upload_fileobj).
    Retorna o object key para armazenar em lesson.video_url.
    """
    object_key = _build_object_key(lesson_id, ext)

    def _upload() -> None:
        s3_client.upload_fileobj(
            Fileobj=file,
            Bucket=bucket,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )

    await asyncio.to_thread(_upload)
    return object_key


async def get_video_metadata(
    s3_client: Any,
    bucket: str,
    object_key: str,
) -> dict[str, Any]:
    """
    Retorna metadados do objeto (ContentLength, ContentType, etc.)
    via HeadObject — sem transferir o corpo.
    Levanta ClientError se o objeto não existir.
    """

    def _head() -> dict[str, Any]:
        return s3_client.head_object(Bucket=bucket, Key=object_key)

    return await asyncio.to_thread(_head)


async def stream_video(
    s3_client: Any,
    bucket: str,
    object_key: str,
    range_header: str | None = None,
) -> tuple[AsyncGenerator[bytes, None], dict[str, Any]]:
    """
    Retorna um async generator de chunks e os metadados da resposta.
    Suporta Range requests para seeking no player de vídeo.

    Returns:
        (stream, response_metadata)
        response_metadata inclui ContentLength, ContentRange, ContentType, etc.
    """
    kwargs: dict[str, Any] = {"Bucket": bucket, "Key": object_key}
    if range_header:
        kwargs["Range"] = range_header

    def _get_object() -> dict[str, Any]:
        return s3_client.get_object(**kwargs)

    response = await asyncio.to_thread(_get_object)
    body = response["Body"]

    async def _chunk_generator() -> AsyncGenerator[bytes, None]:
        try:
            while True:
                chunk = await asyncio.to_thread(body.read, STREAM_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    metadata = {
        "ContentLength": response["ContentLength"],
        "ContentType": response.get("ContentType", "application/octet-stream"),
        "ContentRange": response.get("ContentRange"),
        "AcceptRanges": response.get("AcceptRanges", "bytes"),
    }

    return _chunk_generator(), metadata


async def delete_video(
    s3_client: Any,
    bucket: str,
    object_key: str,
) -> None:
    """Remove o objeto do bucket. Idempotente — não levanta erro se não existir."""

    def _delete() -> None:
        s3_client.delete_object(Bucket=bucket, Key=object_key)

    await asyncio.to_thread(_delete)


async def upload_image(
    s3_client: Any,
    bucket: str,
    file: IO[bytes],
    prefix: str,
    ext: str,
    content_type: str,
) -> str:
    """
    Faz upload de uma imagem para o MinIO.
    Retorna o object key (ex: thumbnails/{uuid}.jpg).
    """
    object_key = f"{prefix}/{uuid.uuid4()}{ext}"

    def _upload() -> None:
        s3_client.upload_fileobj(
            Fileobj=file,
            Bucket=bucket,
            Key=object_key,
            ExtraArgs={"ContentType": content_type},
        )

    await asyncio.to_thread(_upload)
    return object_key
