# app/core/config.py
"""
Configurações centralizadas da aplicação via variáveis de ambiente.
Usa pydantic-settings para validação e type safety.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Banco de dados ----
    database_url: str = Field(
        default="sqlite+aiosqlite:///./test.db",
        description="URL de conexão SQLAlchemy (asyncpg para Postgres, aiosqlite para testes)",
    )

    # ---- MinIO ----
    minio_root_user: str = Field(default="minio_admin")
    minio_root_password: str = Field(default="")
    minio_api_port: int = Field(default=9000)
    minio_endpoint: str = Field(default="http://minio:9000")
    minio_bucket_name: str = Field(default="course-videos")

    # ---- App ----
    backend_port: int = Field(default=8000)
    frontend_port: int = Field(default=3000)
    secret_key: str = Field(default="dev-secret")
    debug: bool = Field(default=False)

    # ---- Notion (Passo 7) ----
    notion_api_key: str = Field(default="")
    notion_database_id: str = Field(default="")

    # ---- Google (Drive API v3 + YouTube Data API v3) ----
    google_api_key: str = Field(default="")

    # ---- Local Import ----
    imports_path: str = Field(default="/imports")


@lru_cache
def get_settings() -> Settings:
    """
    Retorna instância cacheada das configurações.
    O cache garante que o .env é lido apenas uma vez por processo.
    """
    return Settings()
