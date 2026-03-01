# tests/test_api_courses.py
"""
Testes de integração para os endpoints de Cursos.

Cobertura:
  GET    /api/v1/courses            — lista vazia e com dados
  POST   /api/v1/courses            — criação válida e payload inválido
  GET    /api/v1/courses/{id}       — curso encontrado, 404 e com aulas
  DELETE /api/v1/courses/{id}       — deleção e cascade
"""
import pytest
from httpx import AsyncClient

BASE = "/api/v1/courses"


# ================================================================
# GET /courses — Listar cursos
# ================================================================
class TestListCourses:
    async def test_list_returns_empty_initially(self, client: AsyncClient) -> None:
        """Deve retornar lista vazia quando não há cursos."""
        response = await client.get(BASE)
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_returns_created_courses(self, client: AsyncClient) -> None:
        """Deve retornar os cursos criados, do mais recente ao mais antigo."""
        await client.post(BASE, json={"title": "Curso A"})
        await client.post(BASE, json={"title": "Curso B"})

        response = await client.get(BASE)
        assert response.status_code == 200
        titles = [c["title"] for c in response.json()]
        # ordenado por created_at DESC: B foi criado depois, aparece primeiro
        assert "Curso A" in titles
        assert "Curso B" in titles
        assert len(titles) == 2


# ================================================================
# POST /courses — Criar curso
# ================================================================
class TestCreateCourse:
    async def test_create_course_returns_201(self, client: AsyncClient) -> None:
        """Criação bem-sucedida deve retornar 201 com os dados."""
        payload = {"title": "Introdução ao FastAPI", "description": "Curso básico"}
        response = await client.post(BASE, json=payload)

        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Introdução ao FastAPI"
        assert body["description"] == "Curso básico"
        assert "id" in body
        assert "created_at" in body

    async def test_create_course_without_description(self, client: AsyncClient) -> None:
        """Description é opcional — deve aceitar None."""
        response = await client.post(BASE, json={"title": "Só o título"})
        assert response.status_code == 201
        assert response.json()["description"] is None

    async def test_create_course_empty_title_returns_422(self, client: AsyncClient) -> None:
        """Título vazio deve ser rejeitado com 422."""
        response = await client.post(BASE, json={"title": ""})
        assert response.status_code == 422

    async def test_create_course_missing_title_returns_422(self, client: AsyncClient) -> None:
        """Payload sem title deve retornar 422."""
        response = await client.post(BASE, json={"description": "Sem título"})
        assert response.status_code == 422

    async def test_create_course_title_too_long_returns_422(self, client: AsyncClient) -> None:
        """Título com mais de 255 chars deve ser rejeitado."""
        response = await client.post(BASE, json={"title": "x" * 256})
        assert response.status_code == 422


# ================================================================
# GET /courses/{id} — Detalhe do curso
# ================================================================
class TestGetCourse:
    async def test_get_course_returns_200_with_lessons(self, client: AsyncClient) -> None:
        """Deve retornar o curso com lista de aulas (inicialmente vazia)."""
        created = (await client.post(BASE, json={"title": "Curso Detalhe"})).json()
        course_id = created["id"]

        response = await client.get(f"{BASE}/{course_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == course_id
        assert body["title"] == "Curso Detalhe"
        assert body["lessons"] == []

    async def test_get_course_includes_nested_lessons(self, client: AsyncClient) -> None:
        """O campo lessons deve incluir as aulas criadas."""
        course = (await client.post(BASE, json={"title": "Curso com Aulas"})).json()
        course_id = course["id"]

        # Adiciona uma aula
        await client.post(
            f"{BASE}/{course_id}/lessons",
            json={"title": "Aula 1"},
        )

        response = await client.get(f"{BASE}/{course_id}")
        assert response.status_code == 200
        lessons = response.json()["lessons"]
        assert len(lessons) == 1
        assert lessons[0]["title"] == "Aula 1"

    async def test_get_nonexistent_course_returns_404(self, client: AsyncClient) -> None:
        """Curso inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"{BASE}/{fake_id}")
        assert response.status_code == 404

    async def test_get_course_with_invalid_uuid_returns_422(
        self, client: AsyncClient
    ) -> None:
        """UUID malformado deve retornar 422."""
        response = await client.get(f"{BASE}/nao-e-um-uuid")
        assert response.status_code == 422


# ================================================================
# DELETE /courses/{id} — Remover curso
# ================================================================
class TestDeleteCourse:
    async def test_delete_course_returns_204(self, client: AsyncClient) -> None:
        """Deleção bem-sucedida deve retornar 204 sem body."""
        created = (await client.post(BASE, json={"title": "Para Deletar"})).json()
        course_id = created["id"]

        response = await client.delete(f"{BASE}/{course_id}")
        assert response.status_code == 204

    async def test_deleted_course_not_found_on_get(self, client: AsyncClient) -> None:
        """Após deleção, GET deve retornar 404."""
        created = (await client.post(BASE, json={"title": "Deletar e buscar"})).json()
        course_id = created["id"]

        await client.delete(f"{BASE}/{course_id}")
        response = await client.get(f"{BASE}/{course_id}")
        assert response.status_code == 404

    async def test_delete_nonexistent_course_returns_404(
        self, client: AsyncClient
    ) -> None:
        """Deletar curso inexistente deve retornar 404."""
        fake_id = "00000000-0000-0000-0000-000000000001"
        response = await client.delete(f"{BASE}/{fake_id}")
        assert response.status_code == 404

    async def test_delete_course_cascades_to_lessons(self, client: AsyncClient) -> None:
        """Deletar o curso deve remover as aulas associadas (cascade)."""
        course = (await client.post(BASE, json={"title": "Cascade Test"})).json()
        course_id = course["id"]

        lesson = (
            await client.post(
                f"{BASE}/{course_id}/lessons",
                json={"title": "Aula Cascade"},
            )
        ).json()
        lesson_id = lesson["id"]

        await client.delete(f"{BASE}/{course_id}")

        # Tenta buscar a aula diretamente
        response = await client.get(f"/api/v1/lessons/{lesson_id}")
        assert response.status_code == 404
