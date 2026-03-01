# app/models/__init__.py
"""
Importa todos os modelos para que o Alembic os detecte automaticamente
no processo de geração de migrações.
"""
from app.models.base import Base
from app.models.course import Course
from app.models.module import Module
from app.models.lesson import Lesson
from app.models.note import Note

__all__ = ["Base", "Course", "Module", "Lesson", "Note"]
