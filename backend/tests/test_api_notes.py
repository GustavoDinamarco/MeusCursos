# tests/test_api_notes.py
"""
Testes de integração para os endpoints de Anotações.

Cobertura:
  POST   /api/v1/lessons/{id}/notes  — criação com timestamp, validações
  GET    /api/v1/lessons/{id}/notes  — listagem ordenada por timestamp
  DELETE /api/v1/notes/{id}          — remoção
"""
import pytest
from httpx import AsyncClient

COURSES_BASE = "/api/v1/courses"
LESSONS_BASE = "/api/v1/lessons"
NOTES_BASE = "/api/v1/notes"


# ================================================================
# Helpers
# ================================================================
async def create_course_and_lesson(
    client: AsyncClient,
) -> tuple[str, str]:
    """Cria um curso + aula auxiliar e retorna (course_id, lesson_id)."""
    course = (
        await client.post(COURSES_BASE, json={"title": "Curso para Notes"})
    ).json()
    lesson = (
        await client.post(
            f"{COURSES_BASE}/{course['id']}/lessons",
            json={"title": "Aula para Notes"},
        )
    ).json()
    return course["id"], lesson["id"]


# ================================================================
# POST /lessons/{id}/notes — Criar anotação
# ================================================================
class TestCreateNote:
    async def test_create_note_returns_201(self, client: AsyncClient) -> None:
        """Anotação válida deve retornar 201 com dados corretos."""
        _, lesson_id = await create_course_and_lesson(client)

        payload = {"content": "Conceito importante", "video_timestamp": 125}
        response = await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes", json=payload
        )

        assert response.status_code == 201
        body = response.json()
        assert body["content"] == "Conceito importante"
        assert body["video_timestamp"] == 125
        assert body["lesson_id"] == lesson_id
        assert "id" in body
        assert "created_at" in body

    async def test_create_note_with_zero_timestamp(
        self, client: AsyncClient
    ) -> None:
        """Timestamp zero (início do vídeo) é válido."""
        _, lesson_id = await create_course_and_lesson(client)

        payload = {"content": "Nota no início", "video_timestamp": 0}
        response = await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes", json=payload
        )

        assert response.status_code == 201
        assert response.json()["video_timestamp"] == 0

    async def test_create_note_on_nonexistent_lesson_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Anotação em aula inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000099"
        response = await client.post(
            f"{LESSONS_BASE}/{fake_id}/notes",
            json={"content": "Nota órfã", "video_timestamp": 10},
        )
        assert response.status_code == 404

    async def test_create_note_empty_content_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Conteúdo vazio deve retornar 422."""
        _, lesson_id = await create_course_and_lesson(client)
        response = await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "", "video_timestamp": 10},
        )
        assert response.status_code == 422

    async def test_create_note_negative_timestamp_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Timestamp negativo deve retornar 422."""
        _, lesson_id = await create_course_and_lesson(client)
        response = await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Nota inválida", "video_timestamp": -5},
        )
        assert response.status_code == 422

    async def test_create_note_missing_fields_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Payload sem campos obrigatórios deve retornar 422."""
        _, lesson_id = await create_course_and_lesson(client)
        response = await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={},
        )
        assert response.status_code == 422


# ================================================================
# GET /lessons/{id}/notes — Listar anotações
# ================================================================
class TestListNotes:
    async def test_list_notes_returns_empty_initially(
        self, client: AsyncClient
    ) -> None:
        """Aula sem anotações retorna lista vazia."""
        _, lesson_id = await create_course_and_lesson(client)
        response = await client.get(f"{LESSONS_BASE}/{lesson_id}/notes")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_notes_returns_created_notes(
        self, client: AsyncClient
    ) -> None:
        """Anotações criadas devem aparecer na listagem."""
        _, lesson_id = await create_course_and_lesson(client)

        await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Primeira nota", "video_timestamp": 30},
        )
        await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Segunda nota", "video_timestamp": 90},
        )

        response = await client.get(f"{LESSONS_BASE}/{lesson_id}/notes")
        assert response.status_code == 200
        notes = response.json()
        assert len(notes) == 2

    async def test_list_notes_ordered_by_timestamp(
        self, client: AsyncClient
    ) -> None:
        """Notas devem ser ordenadas por video_timestamp ASC."""
        _, lesson_id = await create_course_and_lesson(client)

        # Cria notas fora de ordem
        await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Nota no meio", "video_timestamp": 120},
        )
        await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Nota no fim", "video_timestamp": 300},
        )
        await client.post(
            f"{LESSONS_BASE}/{lesson_id}/notes",
            json={"content": "Nota no início", "video_timestamp": 10},
        )

        response = await client.get(f"{LESSONS_BASE}/{lesson_id}/notes")
        notes = response.json()
        timestamps = [n["video_timestamp"] for n in notes]
        assert timestamps == [10, 120, 300]

    async def test_list_notes_nonexistent_lesson_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Listar notas de aula inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000098"
        response = await client.get(f"{LESSONS_BASE}/{fake_id}/notes")
        assert response.status_code == 404


# ================================================================
# DELETE /notes/{id} — Remover anotação
# ================================================================
class TestDeleteNote:
    async def test_delete_note_returns_204(self, client: AsyncClient) -> None:
        """Remoção bem-sucedida retorna 204."""
        _, lesson_id = await create_course_and_lesson(client)
        note = (
            await client.post(
                f"{LESSONS_BASE}/{lesson_id}/notes",
                json={"content": "Nota temporária", "video_timestamp": 50},
            )
        ).json()

        response = await client.delete(f"{NOTES_BASE}/{note['id']}")
        assert response.status_code == 204

    async def test_delete_nonexistent_note_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Remover nota inexistente retorna 404."""
        fake_id = "00000000-0000-0000-0000-000000000097"
        response = await client.delete(f"{NOTES_BASE}/{fake_id}")
        assert response.status_code == 404

    async def test_deleted_note_gone_from_list(
        self, client: AsyncClient
    ) -> None:
        """Nota removida não aparece mais na listagem."""
        _, lesson_id = await create_course_and_lesson(client)

        note = (
            await client.post(
                f"{LESSONS_BASE}/{lesson_id}/notes",
                json={"content": "Nota a ser removida", "video_timestamp": 75},
            )
        ).json()

        await client.delete(f"{NOTES_BASE}/{note['id']}")

        response = await client.get(f"{LESSONS_BASE}/{lesson_id}/notes")
        note_ids = [n["id"] for n in response.json()]
        assert note["id"] not in note_ids

    async def test_delete_note_invalid_uuid_returns_422(
        self, client: AsyncClient
    ) -> None:
        """UUID inválido retorna 422."""
        response = await client.delete(f"{NOTES_BASE}/nao-e-uuid")
        assert response.status_code == 422
