# tests/test_api_notion.py
"""
Testes de integração para exportação de anotações ao Notion.

Estratégia de mock:
  - get_notion_client e export_notes_to_notion são mockados no módulo
    app.api.notes (onde são importados), evitando chamadas reais à API.
  - get_settings é mockado para simular Notion configurado/não configurado.

Cobertura:
  POST /api/v1/lessons/{id}/export-notion
"""
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient

COURSES = "/api/v1/courses"
LESSONS = "/api/v1/lessons"

FAKE_NOTION_URL = "https://www.notion.so/Curso-Aula-abc123"


# ================================================================
# Helpers
# ================================================================
async def create_course_and_lesson(
    client: AsyncClient,
) -> tuple[str, str]:
    """Cria curso + aula auxiliar e retorna (course_id, lesson_id)."""
    course = (
        await client.post(COURSES, json={"title": "Curso Notion"})
    ).json()
    lesson = (
        await client.post(
            f"{COURSES}/{course['id']}/lessons",
            json={"title": "Aula Notion"},
        )
    ).json()
    return course["id"], lesson["id"]


async def create_note(
    client: AsyncClient,
    lesson_id: str,
    content: str = "Nota de teste",
    timestamp: int = 60,
) -> dict:
    """Cria uma anotação auxiliar."""
    return (
        await client.post(
            f"{LESSONS}/{lesson_id}/notes",
            json={"content": content, "video_timestamp": timestamp},
        )
    ).json()


# ================================================================
# POST /lessons/{id}/export-notion — Exportar para Notion
# ================================================================
class TestExportToNotion:
    @patch("app.api.notes.export_notes_to_notion", new_callable=AsyncMock)
    @patch("app.api.notes.get_notion_client")
    @patch("app.api.notes.get_settings")
    async def test_export_returns_200_with_notion_url(
        self,
        mock_settings: MagicMock,
        mock_get_client: MagicMock,
        mock_export: AsyncMock,
        client: AsyncClient,
    ) -> None:
        """Exportação válida retorna 200 com notion_url."""
        mock_settings.return_value = MagicMock(
            notion_api_key="ntn_fake_key",
            notion_database_id="fake-db-id",
        )
        mock_get_client.return_value = MagicMock()
        mock_export.return_value = FAKE_NOTION_URL

        _, lesson_id = await create_course_and_lesson(client)
        await create_note(client, lesson_id, "Conceito X", 30)
        await create_note(client, lesson_id, "Conceito Y", 90)

        response = await client.post(
            f"{LESSONS}/{lesson_id}/export-notion"
        )

        assert response.status_code == 200
        assert response.json()["notion_url"] == FAKE_NOTION_URL
        mock_export.assert_awaited_once()

    @patch("app.api.notes.export_notes_to_notion", new_callable=AsyncMock)
    @patch("app.api.notes.get_notion_client")
    @patch("app.api.notes.get_settings")
    async def test_export_passes_correct_data_to_service(
        self,
        mock_settings: MagicMock,
        mock_get_client: MagicMock,
        mock_export: AsyncMock,
        client: AsyncClient,
    ) -> None:
        """Verifica que título do curso e aula são passados ao serviço."""
        mock_settings.return_value = MagicMock(
            notion_api_key="ntn_key",
            notion_database_id="db-id",
        )
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_export.return_value = FAKE_NOTION_URL

        _, lesson_id = await create_course_and_lesson(client)
        await create_note(client, lesson_id)

        await client.post(f"{LESSONS}/{lesson_id}/export-notion")

        # Verifica argumentos: notion_client, notes, lesson_title, course_title
        call_args = mock_export.call_args
        assert call_args[0][0] is mock_client  # notion_client
        assert len(call_args[0][1]) == 1  # 1 nota
        assert call_args[0][2] == "Aula Notion"  # lesson_title
        assert call_args[0][3] == "Curso Notion"  # course_title

    @patch("app.api.notes.get_settings")
    async def test_export_without_notion_config_returns_400(
        self,
        mock_settings: MagicMock,
        client: AsyncClient,
    ) -> None:
        """Notion não configurado retorna 400."""
        mock_settings.return_value = MagicMock(
            notion_api_key="",
            notion_database_id="",
        )

        _, lesson_id = await create_course_and_lesson(client)
        await create_note(client, lesson_id)

        response = await client.post(
            f"{LESSONS}/{lesson_id}/export-notion"
        )

        assert response.status_code == 400
        assert "Notion não configurado" in response.json()["detail"]

    @patch("app.api.notes.get_settings")
    async def test_export_nonexistent_lesson_returns_404(
        self,
        mock_settings: MagicMock,
        client: AsyncClient,
    ) -> None:
        """Aula inexistente retorna 404."""
        mock_settings.return_value = MagicMock(
            notion_api_key="ntn_key",
            notion_database_id="db-id",
        )

        fake_id = "00000000-0000-0000-0000-000000000090"
        response = await client.post(
            f"{LESSONS}/{fake_id}/export-notion"
        )

        assert response.status_code == 404

    @patch("app.api.notes.get_settings")
    async def test_export_lesson_without_notes_returns_400(
        self,
        mock_settings: MagicMock,
        client: AsyncClient,
    ) -> None:
        """Aula sem anotações retorna 400."""
        mock_settings.return_value = MagicMock(
            notion_api_key="ntn_key",
            notion_database_id="db-id",
        )

        _, lesson_id = await create_course_and_lesson(client)

        response = await client.post(
            f"{LESSONS}/{lesson_id}/export-notion"
        )

        assert response.status_code == 400
        assert "Nenhuma anotação" in response.json()["detail"]

    @patch("app.api.notes.export_notes_to_notion", new_callable=AsyncMock)
    @patch("app.api.notes.get_notion_client")
    @patch("app.api.notes.get_settings")
    async def test_export_notion_api_error_returns_502(
        self,
        mock_settings: MagicMock,
        mock_get_client: MagicMock,
        mock_export: AsyncMock,
        client: AsyncClient,
    ) -> None:
        """Erro na API do Notion retorna 502 Bad Gateway."""
        mock_settings.return_value = MagicMock(
            notion_api_key="ntn_key",
            notion_database_id="db-id",
        )
        mock_get_client.return_value = MagicMock()
        mock_export.side_effect = Exception("Notion API error")

        _, lesson_id = await create_course_and_lesson(client)
        await create_note(client, lesson_id)

        response = await client.post(
            f"{LESSONS}/{lesson_id}/export-notion"
        )

        assert response.status_code == 502
        assert "Erro ao exportar para o Notion" in response.json()["detail"]


# ================================================================
# Testes unitários — notion_service helpers
# ================================================================
class TestNotionServiceHelpers:
    def test_format_timestamp_zero(self) -> None:
        from app.services.notion_service import _format_timestamp

        assert _format_timestamp(0) == "0:00"

    def test_format_timestamp_seconds(self) -> None:
        from app.services.notion_service import _format_timestamp

        assert _format_timestamp(45) == "0:45"

    def test_format_timestamp_minutes_and_seconds(self) -> None:
        from app.services.notion_service import _format_timestamp

        assert _format_timestamp(125) == "2:05"

    def test_build_note_blocks_structure(self) -> None:
        from unittest.mock import MagicMock

        from app.services.notion_service import _build_note_blocks

        note1 = MagicMock()
        note1.video_timestamp = 30
        note1.content = "Primeira nota"

        note2 = MagicMock()
        note2.video_timestamp = 120
        note2.content = "Segunda nota"

        blocks = _build_note_blocks([note1, note2])

        # 1 heading + 2 bulleteds
        assert len(blocks) == 3
        assert blocks[0]["type"] == "heading_2"
        assert blocks[1]["type"] == "bulleted_list_item"
        assert blocks[2]["type"] == "bulleted_list_item"

        # Verifica conteúdo do primeiro bullet
        rich_text = blocks[1]["bulleted_list_item"]["rich_text"]
        assert "[0:30]" in rich_text[0]["text"]["content"]
        assert rich_text[1]["text"]["content"] == "Primeira nota"
