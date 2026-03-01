# tests/conftest.py
"""
Fixtures compartilhadas entre todos os testes.

Estratégia de banco:
  - SQLite em memória com aiosqlite — sem dependência de Docker.
  - Fixtures de modelos: sessão com rollback (isolamento por SAVEPOINT).
  - Fixtures de API: AsyncClient com override de get_db + DELETE entre testes.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.database import get_db
from app.main import app
from app.models.base import Base
# side-effect: registra todos os modelos nos metadados
from app.models import Course, Lesson, Note  # noqa: F401

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# ================================================================
# Engine compartilhado por toda a sessão de testes
# ================================================================
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    """
    Engine único criado uma vez por sessão.
    Cria as tabelas no início e as destrói ao final.
    """
    _engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield _engine

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


# ================================================================
# Fixture de sessão — para testes de modelos (com rollback)
# ================================================================
@pytest.fixture
async def db(engine) -> AsyncSession:  # type: ignore[override]
    """
    Sessão isolada por teste via rollback.
    Usada nos testes de model direto (sem API).
    """
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


# ================================================================
# Fixture de cliente HTTP — para testes de endpoints FastAPI
# ================================================================
@pytest.fixture
async def client(engine):
    """
    AsyncClient configurado com o app FastAPI.

    - Substitui get_db pelo engine de teste (SQLite in-memory).
    - Após cada teste, limpa todas as tabelas para isolamento.
    """
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncSession:  # type: ignore[override]
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Limpa todas as tabelas respeitando a ordem de FK (reversed = filhas primeiro)
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())

    app.dependency_overrides.clear()
