# app/core/database.py
"""
Engine assíncrono SQLAlchemy e fábrica de sessões.
Segue o padrão Unit of Work via AsyncSession.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

settings = get_settings()

# create_async_engine é thread-safe e deve ser criado uma única vez por processo.
# pool_pre_ping garante que conexões mortas sejam detectadas antes do uso.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,      # loga SQL apenas em modo debug
    pool_pre_ping=True,
    # Para SQLite (testes), desabilitar check_same_thread
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {},
)

# Fábrica de sessões: expire_on_commit=False evita lazy-load após commit
# em contextos assíncronos.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection do FastAPI.
    Garante que a sessão é fechada ao fim de cada request,
    mesmo em caso de exceção.

    Uso:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
