# tests/test_api_lessons.py
"""
Testes de integração para os endpoints de Aulas.

Cobertura:
  POST /api/v1/courses/{id}/lessons — criação válida, 404 de curso, payload inválido
  GET  /api/v1/lessons/{id}         — aula encontrada e 404
"""
import pytest
from httpx import AsyncClient

COURSES_BASE = "/api/v1/courses"
LESSONS_BASE = "/api/v1/lessons"


# ================================================================
# Helpers
# ================================================================
async def create_course(client: AsyncClient, title: str = "Curso Helper") -> dict:
    response = await client.post(COURSES_BASE, json={"title": title})
    assert response.status_code == 201
    return response.json()


# ================================================================
# POST /courses/{id}/lessons — Criar aula
# ================================================================
class TestCreateLesson:
    async def test_create_lesson_returns_201(self, client: AsyncClient) -> None:
        """Criação de aula válida deve retornar 201 com dados corretos."""
        course = await create_course(client)
        course_id = course["id"]

        payload = {"title": "Aula 01 — Introdução", "description": "Primeira aula"}
        response = await client.post(
            f"{COURSES_BASE}/{course_id}/lessons", json=payload
        )

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Aula 01 — Introdução"
        assert body["description"] == "Primeira aula"
        assert body["course_id"] == course_id
        assert body["video_url"] is None
        assert "id" in body
        assert "created_at" in body

    async def test_create_lesson_without_description(self, client: AsyncClient) -> None:
        """Description é opcional."""
        course = await create_course(client, "Curso Sem Desc")
        response = await client.post(
            f"{COURSES_BASE}/{course['id']}/lessons",
            json={"title": "Aula Simples"},
        )
        assert response.status_code == 201
        assert response.json()["description"] is None

    async def test_create_lesson_on_nonexistent_course_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Adicionar aula a curso inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000002"
        response = await client.post(
            f"{COURSES_BASE}/{fake_id}/lessons",
            json={"title": "Aula Órfã"},
        )
        assert response.status_code == 404

    async def test_create_lesson_empty_title_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Título vazio deve retornar 422."""
        course = await create_course(client, "Curso Validação")
        response = await client.post(
            f"{COURSES_BASE}/{course['id']}/lessons",
            json={"title": ""},
        )
        assert response.status_code == 422

    async def test_create_lesson_missing_title_returns_422(
        self, client: AsyncClient
    ) -> None:
        """Payload sem title deve retornar 422."""
        course = await create_course(client, "Curso Validação 2")
        response = await client.post(
            f"{COURSES_BASE}/{course['id']}/lessons",
            json={"description": "Sem título"},
        )
        assert response.status_code == 422

    async def test_create_multiple_lessons_for_same_course(
        self, client: AsyncClient
    ) -> None:
        """Deve ser possível criar múltiplas aulas no mesmo curso."""
        course = await create_course(client, "Curso Multi-Aulas")
        course_id = course["id"]

        titles = ["Aula 1", "Aula 2", "Aula 3"]
        for title in titles:
            resp = await client.post(
                f"{COURSES_BASE}/{course_id}/lessons",
                json={"title": title},
            )
            assert resp.status_code == 201

        # Verifica via GET /courses/{id} que as 3 aulas estão presentes
        detail = await client.get(f"{COURSES_BASE}/{course_id}")
        assert len(detail.json()["lessons"]) == 3

    async def test_lesson_appears_in_course_detail(self, client: AsyncClient) -> None:
        """Aula criada deve aparecer no GET /courses/{id}."""
        course = await create_course(client, "Curso Aparecer")
        course_id = course["id"]

        lesson_resp = await client.post(
            f"{COURSES_BASE}/{course_id}/lessons",
            json={"title": "Aula Verificável"},
        )
        lesson_id = lesson_resp.json()["id"]

        detail = await client.get(f"{COURSES_BASE}/{course_id}")
        lesson_ids_in_course = [l["id"] for l in detail.json()["lessons"]]
        assert lesson_id in lesson_ids_in_course


# ================================================================
# GET /lessons/{id} — Detalhe de aula
# ================================================================
class TestGetLesson:
    async def test_get_lesson_returns_200(self, client: AsyncClient) -> None:
        """GET de aula existente deve retornar 200 com dados."""
        course = await create_course(client, "Curso GET Aula")
        lesson = (
            await client.post(
                f"{COURSES_BASE}/{course['id']}/lessons",
                json={"title": "Aula para GET"},
            )
        ).json()

        response = await client.get(f"{LESSONS_BASE}/{lesson['id']}")
        assert response.status_code == 200
        assert response.json()["title"] == "Aula para GET"

    async def test_get_nonexistent_lesson_returns_404(
        self, client: AsyncClient
    ) -> None:
        """GET de aula inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000003"
        response = await client.get(f"{LESSONS_BASE}/{fake_id}")
        assert response.status_code == 404

    async def test_get_lesson_with_invalid_uuid_returns_422(
        self, client: AsyncClient
    ) -> None:
        """UUID inválido deve retornar 422."""
        response = await client.get(f"{LESSONS_BASE}/nao-e-uuid")
        assert response.status_code == 422
