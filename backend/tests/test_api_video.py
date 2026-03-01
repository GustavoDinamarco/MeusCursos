# tests/test_api_video.py
"""
Testes de integração para upload e streaming de vídeo.

Estratégia de mock:
  - As funções do minio_service são mockadas no módulo app.api.lessons
    (onde são importadas), evitando dependência real do MinIO.
  - O banco de dados usa SQLite em memória via a fixture `client`.

Cobertura:
  POST /api/v1/lessons/{id}/upload-video
  GET  /api/v1/lessons/{id}/video
  Funções utilitárias de minio_service (validate_video_extension)
"""
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

COURSES = "/api/v1/courses"
LESSONS = "/api/v1/lessons"


# ================================================================
# Helpers
# ================================================================
async def create_course_and_lesson(
    client: AsyncClient,
) -> tuple[str, str]:
    """Cria um curso com uma aula e retorna (course_id, lesson_id)."""
    course = (await client.post(COURSES, json={"title": "Video Course"})).json()
    lesson = (
        await client.post(
            f"{COURSES}/{course['id']}/lessons",
            json={"title": "Video Lesson"},
        )
    ).json()
    return course["id"], lesson["id"]


def fake_video_file(
    filename: str = "aula.mp4",
    content: bytes = b"fake-video-content-mp4",
) -> dict:
    """Monta o payload files= para o upload multipart."""
    return {"file": (filename, io.BytesIO(content), "video/mp4")}


# ================================================================
# validate_video_extension — Testes unitários
# ================================================================
class TestValidateVideoExtension:
    def test_valid_mp4(self) -> None:
        from app.services.minio_service import validate_video_extension

        ext, ct = validate_video_extension("aula.mp4")
        assert ext == ".mp4"
        assert ct == "video/mp4"

    def test_valid_mkv(self) -> None:
        from app.services.minio_service import validate_video_extension

        ext, ct = validate_video_extension("video.MKV")
        assert ext == ".mkv"
        assert ct == "video/x-matroska"

    def test_valid_webm(self) -> None:
        from app.services.minio_service import validate_video_extension

        ext, ct = validate_video_extension("demo.webm")
        assert ext == ".webm"
        assert ct == "video/webm"

    def test_invalid_txt_raises(self) -> None:
        from app.services.minio_service import validate_video_extension

        with pytest.raises(ValueError, match="não permitida"):
            validate_video_extension("notas.txt")

    def test_invalid_pdf_raises(self) -> None:
        from app.services.minio_service import validate_video_extension

        with pytest.raises(ValueError, match="não permitida"):
            validate_video_extension("slide.pdf")

    def test_no_extension_raises(self) -> None:
        from app.services.minio_service import validate_video_extension

        with pytest.raises(ValueError, match="não permitida"):
            validate_video_extension("arquivo_sem_extensao")


# ================================================================
# POST /lessons/{id}/upload-video — Testes de upload
# ================================================================
class TestUploadVideo:
    @patch("app.api.lessons.upload_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_upload_returns_200_and_updates_video_url(
        self, mock_get_s3: MagicMock, mock_upload: AsyncMock, client: AsyncClient
    ) -> None:
        """Upload válido deve retornar a lesson com video_url atualizado."""
        _, lesson_id = await create_course_and_lesson(client)

        mock_get_s3.return_value = MagicMock()
        mock_upload.return_value = f"lessons/{lesson_id}/abc123.mp4"

        response = await client.post(
            f"{LESSONS}/{lesson_id}/upload-video",
            files=fake_video_file(),
        )

        assert response.status_code == 200
        body = response.json()
        assert body["video_url"] == f"lessons/{lesson_id}/abc123.mp4"
        assert body["id"] == lesson_id
        mock_upload.assert_awaited_once()

    @patch("app.api.lessons.upload_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_upload_to_nonexistent_lesson_returns_404(
        self, mock_get_s3: MagicMock, mock_upload: AsyncMock, client: AsyncClient
    ) -> None:
        """Upload para aula inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000010"
        response = await client.post(
            f"{LESSONS}/{fake_id}/upload-video",
            files=fake_video_file(),
        )
        assert response.status_code == 404
        mock_upload.assert_not_awaited()

    @patch("app.api.lessons.upload_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_upload_invalid_extension_returns_400(
        self, mock_get_s3: MagicMock, mock_upload: AsyncMock, client: AsyncClient
    ) -> None:
        """Extensão inválida (.txt) deve retornar 400."""
        _, lesson_id = await create_course_and_lesson(client)

        response = await client.post(
            f"{LESSONS}/{lesson_id}/upload-video",
            files=fake_video_file(filename="notas.txt", content=b"not a video"),
        )

        assert response.status_code == 400
        assert "não permitida" in response.json()["detail"]
        mock_upload.assert_not_awaited()

    @patch("app.api.lessons.delete_video", new_callable=AsyncMock)
    @patch("app.api.lessons.upload_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_upload_replaces_existing_video(
        self,
        mock_get_s3: MagicMock,
        mock_upload: AsyncMock,
        mock_delete: AsyncMock,
        client: AsyncClient,
    ) -> None:
        """Re-upload deve deletar o vídeo anterior do MinIO."""
        _, lesson_id = await create_course_and_lesson(client)

        mock_get_s3.return_value = MagicMock()
        mock_upload.return_value = f"lessons/{lesson_id}/first.mp4"

        # Primeiro upload
        await client.post(
            f"{LESSONS}/{lesson_id}/upload-video",
            files=fake_video_file(filename="first.mp4"),
        )

        # Segundo upload (deve deletar o primeiro)
        mock_upload.return_value = f"lessons/{lesson_id}/second.mp4"
        response = await client.post(
            f"{LESSONS}/{lesson_id}/upload-video",
            files=fake_video_file(filename="second.mp4"),
        )

        assert response.status_code == 200
        assert response.json()["video_url"] == f"lessons/{lesson_id}/second.mp4"
        mock_delete.assert_awaited_once()

    @patch("app.api.lessons.upload_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_upload_mov_valid(
        self, mock_get_s3: MagicMock, mock_upload: AsyncMock, client: AsyncClient
    ) -> None:
        """Upload de .mov deve ser aceito."""
        _, lesson_id = await create_course_and_lesson(client)
        mock_get_s3.return_value = MagicMock()
        mock_upload.return_value = f"lessons/{lesson_id}/video.mov"

        response = await client.post(
            f"{LESSONS}/{lesson_id}/upload-video",
            files=fake_video_file(filename="video.mov"),
        )
        assert response.status_code == 200


# ================================================================
# GET /lessons/{id}/video — Testes de streaming
# ================================================================
class TestStreamVideo:
    @patch("app.api.lessons.stream_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_stream_returns_200_with_video_content(
        self, mock_get_s3: MagicMock, mock_stream: AsyncMock, client: AsyncClient
    ) -> None:
        """Stream sem Range deve retornar 200 com o corpo do vídeo."""
        _, lesson_id = await create_course_and_lesson(client)

        # Prepara a aula com video_url via upload mockado
        with patch("app.api.lessons.upload_video", new_callable=AsyncMock) as mock_up:
            mock_get_s3.return_value = MagicMock()
            mock_up.return_value = f"lessons/{lesson_id}/test.mp4"
            await client.post(
                f"{LESSONS}/{lesson_id}/upload-video",
                files=fake_video_file(),
            )

        # Configura o mock do stream
        video_bytes = b"fake-video-bytes-stream"

        async def fake_stream():
            yield video_bytes

        mock_stream.return_value = (
            fake_stream(),
            {
                "ContentLength": len(video_bytes),
                "ContentType": "video/mp4",
                "ContentRange": None,
                "AcceptRanges": "bytes",
            },
        )

        response = await client.get(f"{LESSONS}/{lesson_id}/video")

        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert response.headers["accept-ranges"] == "bytes"
        assert response.content == video_bytes

    @patch("app.api.lessons.stream_video", new_callable=AsyncMock)
    @patch("app.api.lessons.get_s3_client")
    async def test_stream_with_range_returns_206(
        self, mock_get_s3: MagicMock, mock_stream: AsyncMock, client: AsyncClient
    ) -> None:
        """Stream com Range deve retornar 206 Partial Content."""
        _, lesson_id = await create_course_and_lesson(client)

        with patch("app.api.lessons.upload_video", new_callable=AsyncMock) as mock_up:
            mock_get_s3.return_value = MagicMock()
            mock_up.return_value = f"lessons/{lesson_id}/range.mp4"
            await client.post(
                f"{LESSONS}/{lesson_id}/upload-video",
                files=fake_video_file(),
            )

        partial_bytes = b"partial-content"

        async def fake_stream():
            yield partial_bytes

        mock_stream.return_value = (
            fake_stream(),
            {
                "ContentLength": len(partial_bytes),
                "ContentType": "video/mp4",
                "ContentRange": "bytes 0-14/1000",
                "AcceptRanges": "bytes",
            },
        )

        response = await client.get(
            f"{LESSONS}/{lesson_id}/video",
            headers={"Range": "bytes=0-14"},
        )

        assert response.status_code == 206
        assert response.headers["content-range"] == "bytes 0-14/1000"
        assert response.content == partial_bytes

    async def test_stream_nonexistent_lesson_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Stream de aula inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000011"
        response = await client.get(f"{LESSONS}/{fake_id}/video")
        assert response.status_code == 404

    async def test_stream_lesson_without_video_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Stream de aula sem vídeo deve retornar 404."""
        _, lesson_id = await create_course_and_lesson(client)
        response = await client.get(f"{LESSONS}/{lesson_id}/video")
        assert response.status_code == 404
        assert "não possui vídeo" in response.json()["detail"]
