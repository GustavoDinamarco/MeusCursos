# app/schemas/__init__.py
from app.schemas.course import CourseCreate, CourseResponse, CourseUpdate, CourseWithLessons
from app.schemas.lesson import LessonCreate, LessonResponse, LessonUpdate
from app.schemas.note import NoteCreate, NoteResponse

__all__ = [
    "CourseCreate", "CourseResponse", "CourseUpdate", "CourseWithLessons",
    "LessonCreate", "LessonResponse", "LessonUpdate",
    "NoteCreate", "NoteResponse",
]
