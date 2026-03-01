# app/api/router.py
"""
Router principal — agrega todos os sub-routers da aplicação.
Registre aqui novos domínios conforme o projeto evolui.
"""
from fastapi import APIRouter

from app.api.courses import router as courses_router
from app.api.imports import local_router as local_imports_router
from app.api.imports import router as imports_router
from app.api.lessons import courses_router as lessons_nested_router
from app.api.lessons import lessons_router
from app.api.modules import courses_router as modules_nested_router
from app.api.modules import modules_router
from app.api.notes import lessons_router as notes_nested_router
from app.api.notes import notes_router

api_router = APIRouter()

api_router.include_router(courses_router)
api_router.include_router(lessons_nested_router)
api_router.include_router(lessons_router)
api_router.include_router(modules_nested_router)
api_router.include_router(modules_router)
api_router.include_router(notes_nested_router)
api_router.include_router(notes_router)
api_router.include_router(imports_router)
api_router.include_router(local_imports_router)
