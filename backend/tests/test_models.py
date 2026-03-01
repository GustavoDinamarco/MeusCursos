# tests/test_models.py
"""
Testes TDD para os modelos Course, Lesson e Note.

Cobertura:
  - Criação de entidades com campos válidos
  - Integridade referencial (FK)
  - Cascade delete
  - Valores padrão
  - Representação __repr__
  - Validações de schema Pydantic
"""
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.lesson import Lesson
from app.models.note import Note
from app.schemas import (
    CourseCreate,
    CourseResponse,
    LessonCreate,
    LessonResponse,
    NoteCreate,
    NoteResponse,
)


# ================================================================
# Helpers
# ================================================================
def make_course(**kwargs) -> Course:
    defaults = {"title": "Curso de Teste", "description": "Descrição do curso"}
    return Course(**{**defaults, **kwargs})


def make_lesson(course_id: uuid.UUID, **kwargs) -> Lesson:
    defaults = {"course_id": course_id, "title": "Aula 1", "description": "Intro"}
    return Lesson(**{**defaults, **kwargs})


def make_note(lesson_id: uuid.UUID, **kwargs) -> Note:
    defaults = {"lesson_id": lesson_id, "content": "Nota importante", "video_timestamp": 90}
    return Note(**{**defaults, **kwargs})


# ================================================================
# Course — Testes de modelo
# ================================================================
class TestCourseModel:
    async def test_create_course_persists_to_db(self, db: AsyncSession) -> None:
        """Deve persistir um Course com os campos corretos."""
        course = make_course()
        db.add(course)
        await db.commit()
        await db.refresh(course)

        result = await db.execute(select(Course).where(Course.id == course.id))
        fetched = result.scalar_one()

        assert fetched.id == course.id
        assert fetched.title == "Curso de Teste"
        assert fetched.description == "Descrição do curso"
        assert fetched.created_at is not None

    async def test_course_id_is_uuid(self, db: AsyncSession) -> None:
        """O ID deve ser gerado automaticamente como UUID."""
        course = make_course(title="UUID Test")
        db.add(course)
        await db.commit()

        assert isinstance(course.id, uuid.UUID)

    async def test_course_description_is_nullable(self, db: AsyncSession) -> None:
        """description pode ser None."""
        course = make_course(description=None)
        db.add(course)
        await db.commit()
        await db.refresh(course)

        assert course.description is None

    async def test_course_repr(self, db: AsyncSession) -> None:
        """__repr__ deve retornar uma string legível."""
        course = make_course()
        db.add(course)
        await db.commit()

        repr_str = repr(course)
        assert "Course" in repr_str
        assert "Curso de Teste" in repr_str

    async def test_two_courses_have_different_ids(self, db: AsyncSession) -> None:
        """IDs devem ser únicos por curso."""
        c1 = make_course(title="Curso A")
        c2 = make_course(title="Curso B")
        db.add_all([c1, c2])
        await db.commit()

        assert c1.id != c2.id


# ================================================================
# Lesson — Testes de modelo
# ================================================================
class TestLessonModel:
    async def test_create_lesson_linked_to_course(self, db: AsyncSession) -> None:
        """Deve criar Lesson vinculada ao Course correto."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id)
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)

        assert lesson.course_id == course.id
        assert lesson.title == "Aula 1"
        assert lesson.video_url is None

    async def test_lesson_video_url_can_be_set(self, db: AsyncSession) -> None:
        """video_url deve ser salvo corretamente."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id, video_url="course-videos/uuid/video.mp4")
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)

        assert lesson.video_url == "course-videos/uuid/video.mp4"

    async def test_lesson_repr(self, db: AsyncSession) -> None:
        """__repr__ deve conter informações da aula."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id, title="Aula Repr")
        db.add(lesson)
        await db.commit()

        repr_str = repr(lesson)
        assert "Lesson" in repr_str
        assert "Aula Repr" in repr_str

    async def test_cascade_delete_course_deletes_lessons(self, db: AsyncSession) -> None:
        """Deletar Course deve remover todas as Lessons via cascade."""
        course = make_course(title="Curso Cascade")
        db.add(course)
        await db.commit()

        lesson1 = make_lesson(course_id=course.id, title="Aula Cascade 1")
        lesson2 = make_lesson(course_id=course.id, title="Aula Cascade 2")
        db.add_all([lesson1, lesson2])
        await db.commit()

        lesson1_id = lesson1.id
        lesson2_id = lesson2.id

        await db.delete(course)
        await db.commit()

        r1 = await db.execute(select(Lesson).where(Lesson.id == lesson1_id))
        r2 = await db.execute(select(Lesson).where(Lesson.id == lesson2_id))

        assert r1.scalar_one_or_none() is None
        assert r2.scalar_one_or_none() is None


# ================================================================
# Note — Testes de modelo
# ================================================================
class TestNoteModel:
    async def test_create_note_with_timestamp(self, db: AsyncSession) -> None:
        """Deve criar Note com o timestamp correto."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id)
        db.add(lesson)
        await db.commit()

        note = make_note(lesson_id=lesson.id, video_timestamp=125)
        db.add(note)
        await db.commit()
        await db.refresh(note)

        assert note.lesson_id == lesson.id
        assert note.content == "Nota importante"
        assert note.video_timestamp == 125

    async def test_note_default_timestamp_is_zero(self, db: AsyncSession) -> None:
        """video_timestamp padrão deve ser 0."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id)
        db.add(lesson)
        await db.commit()

        note = Note(lesson_id=lesson.id, content="Nota sem ts")
        db.add(note)
        await db.commit()
        await db.refresh(note)

        assert note.video_timestamp == 0

    async def test_cascade_delete_lesson_deletes_notes(self, db: AsyncSession) -> None:
        """Deletar Lesson deve remover todas as Notes via cascade."""
        course = make_course()
        db.add(course)
        await db.commit()

        lesson = make_lesson(course_id=course.id)
        db.add(lesson)
        await db.commit()

        note = make_note(lesson_id=lesson.id)
        db.add(note)
        await db.commit()
        note_id = note.id

        await db.delete(lesson)
        await db.commit()

        result = await db.execute(select(Note).where(Note.id == note_id))
        assert result.scalar_one_or_none() is None

    async def test_note_repr(self, db: AsyncSession) -> None:
        """__repr__ deve conter id, lesson e timestamp."""
        course = make_course()
        db.add(course)
        await db.commit()
        lesson = make_lesson(course_id=course.id)
        db.add(lesson)
        await db.commit()

        note = make_note(lesson_id=lesson.id, video_timestamp=42)
        db.add(note)
        await db.commit()

        repr_str = repr(note)
        assert "Note" in repr_str
        assert "42s" in repr_str


# ================================================================
# Schemas Pydantic — Testes de validação
# ================================================================
class TestSchemas:
    def test_course_create_valid(self) -> None:
        schema = CourseCreate(title="Curso Válido", description="Desc")
        assert schema.title == "Curso Válido"

    def test_course_create_empty_title_raises(self) -> None:
        with pytest.raises(ValidationError):
            CourseCreate(title="")

    def test_course_create_title_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            CourseCreate(title="x" * 256)

    def test_note_create_negative_timestamp_raises(self) -> None:
        """video_timestamp não pode ser negativo (ge=0)."""
        with pytest.raises(ValidationError):
            NoteCreate(content="Nota", video_timestamp=-1)

    def test_note_create_zero_timestamp_valid(self) -> None:
        note = NoteCreate(content="Inicio do vídeo", video_timestamp=0)
        assert note.video_timestamp == 0

    def test_lesson_create_valid(self) -> None:
        lesson = LessonCreate(title="Aula Schema")
        assert lesson.title == "Aula Schema"
        assert lesson.description is None

    def test_course_response_from_orm(self, db: AsyncSession) -> None:
        """CourseResponse deve serializar a partir de um model ORM."""
        # Testa a lógica de from_attributes sem precisar do banco
        course_id = uuid.uuid4()
        from datetime import datetime, timezone
        fake_course = Course(
            id=course_id,
            title="ORM Test",
            description="Desc",
            created_at=datetime.now(timezone.utc),
        )
        response = CourseResponse.model_validate(fake_course)
        assert response.id == course_id
        assert response.title == "ORM Test"
