# alembic/env.py
"""
Ambiente de execução do Alembic com suporte a SQLAlchemy assíncrono.

Padrão oficial: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
"""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

# Importa Base DEPOIS dos models para garantir que os metadados estejam populados
from app.models import Base  # noqa: F401 — side-effect import (registra todos os models)
from app.core.config import get_settings

# ---------------------------------------------------------------
# Configuração padrão do Alembic (lida do alembic.ini)
# ---------------------------------------------------------------
config = context.config
settings = get_settings()

# Substitui a URL placeholder do alembic.ini pela URL real das variáveis de ambiente.
# Isso evita credenciais hardcoded no alembic.ini.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configura o logging se o alembic.ini tiver seção [loggers]
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData alvo para a geração de migrações automáticas (--autogenerate)
target_metadata = Base.metadata


# ---------------------------------------------------------------
# Migrações OFFLINE (sem conexão ativa ao banco)
# Gera SQL puro para execução manual.
# ---------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------
# Migrações ONLINE com engine assíncrono
# ---------------------------------------------------------------
def do_run_migrations(connection):  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria o engine assíncrono e executa as migrações."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # sem pool para migrations
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------
# Ponto de entrada do Alembic
# ---------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
