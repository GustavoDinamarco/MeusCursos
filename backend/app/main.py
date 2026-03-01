# app/main.py
"""
Entry point da aplicação FastAPI.
Os routers de cada domínio serão registrados aqui nos passos seguintes.
"""
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import engine
from app.models import Base

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação:
    - startup: conexões, caches, etc.
    - shutdown: encerramento limpo de recursos.
    """
    # Startup: create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine connections
    await engine.dispose()


app = FastAPI(
    title="Course Platform API",
    version="0.1.0",
    description="API da plataforma local de cursos com anotações por timestamp.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — liberado para localhost em desenvolvimento.
# Em produção, restringir origins conforme necessário.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        f"http://localhost:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
async def health_check() -> dict[str, str]:
    """Endpoint de health check para o Docker e CI."""
    return {"status": "ok"}


# Registra todos os routers sob o prefixo /api/v1
app.include_router(api_router, prefix="/api/v1")
