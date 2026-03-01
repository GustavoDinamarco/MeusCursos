# app/services/notion_service.py
"""
Serviço de exportação para o Notion — cria páginas com anotações
de uma aula no database configurado.

Usa notion-client (sync) com asyncio.to_thread() para não bloquear
o event loop, seguindo o mesmo padrão de minio_service.py.
"""
import asyncio
from typing import Any

from notion_client import Client as NotionClient

from app.core.config import get_settings
from app.models.note import Note


def get_notion_client() -> NotionClient:
    """Cria e retorna um cliente Notion autenticado."""
    settings = get_settings()
    return NotionClient(auth=settings.notion_api_key)


def _format_timestamp(seconds: int) -> str:
    """Converte inteiro de segundos para formato m:ss."""
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def _build_note_blocks(notes: list[Note]) -> list[dict[str, Any]]:
    """
    Monta blocos Notion a partir da lista de notas.
    Cada nota vira um bulleted_list_item com [timestamp] prefix.
    """
    blocks: list[dict[str, Any]] = []

    # Heading
    blocks.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [
                {"type": "text", "text": {"content": "Anotações do vídeo"}}
            ]
        },
    })

    for note in notes:
        ts = _format_timestamp(note.video_timestamp)
        blocks.append({
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": f"[{ts}] "},
                        "annotations": {"bold": True, "color": "blue"},
                    },
                    {
                        "type": "text",
                        "text": {"content": note.content},
                    },
                ]
            },
        })

    return blocks


async def export_notes_to_notion(
    notion_client: NotionClient,
    notes: list[Note],
    lesson_title: str,
    course_title: str,
) -> str:
    """
    Cria uma página no Notion database configurado com as anotações da aula.

    Returns:
        URL da página criada no Notion.
    """
    settings = get_settings()
    database_id = settings.notion_database_id

    page_title = f"{course_title} — {lesson_title}"
    children = _build_note_blocks(notes)

    def _create_page() -> dict[str, Any]:
        return notion_client.pages.create(
            parent={"database_id": database_id},
            properties={
                "title": {
                    "title": [
                        {"type": "text", "text": {"content": page_title}}
                    ]
                }
            },
            children=children,
        )

    response = await asyncio.to_thread(_create_page)
    return response["url"]
