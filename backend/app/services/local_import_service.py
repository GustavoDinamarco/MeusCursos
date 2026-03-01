# app/services/local_import_service.py
"""
Serviço de importação local — lista e valida arquivos de vídeo
em uma pasta montada no container (read-only).

Segurança:
  - Validação de path traversal (impede escapes via '..' ou symlinks)
  - Volume montado como read-only no Docker
  - Apenas extensões de vídeo permitidas
"""
import asyncio
import os
from pathlib import Path

from app.core.config import get_settings
from app.services.minio_service import ALLOWED_EXTENSIONS


def _get_imports_root() -> Path:
    """Retorna o diretório raiz de imports configurado."""
    return Path(get_settings().imports_path)


def check_imports_available() -> bool:
    """Verifica se o diretório de imports existe e é legível."""
    root = _get_imports_root()
    return root.is_dir() and os.access(root, os.R_OK)


def validate_path(subpath: str) -> Path:
    """
    Resolve um subcaminho relativo ao diretório de imports.
    Levanta ValueError se o caminho escapa da raiz (path traversal).
    """
    root = _get_imports_root().resolve()
    # Normaliza e resolve o caminho completo
    target = (root / subpath).resolve()
    # Verifica que o alvo está dentro da raiz
    if not str(target).startswith(str(root)):
        raise ValueError("Caminho inválido: tentativa de path traversal.")
    if not target.exists():
        raise ValueError(f"Caminho não encontrado: {subpath}")
    return target


def _is_video_file(filename: str) -> bool:
    """Verifica se o arquivo tem extensão de vídeo permitida."""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def _list_entries_sync(subpath: str) -> list[dict]:
    """
    Lista diretórios e arquivos de vídeo em um subcaminho.
    Retorna lista ordenada: diretórios primeiro, depois arquivos por nome.
    """
    target = validate_path(subpath)
    if not target.is_dir():
        raise ValueError(f"O caminho não é um diretório: {subpath}")

    dirs: list[dict] = []
    files: list[dict] = []

    for entry in sorted(target.iterdir(), key=lambda e: e.name.lower()):
        # Ignora arquivos ocultos e symlinks que apontam para fora
        if entry.name.startswith("."):
            continue

        rel_path = str(entry.relative_to(_get_imports_root().resolve()))
        # Normaliza para separador /
        rel_path = rel_path.replace("\\", "/")

        if entry.is_dir():
            dirs.append({
                "name": entry.name,
                "type": "directory",
                "path": rel_path,
            })
        elif entry.is_file() and _is_video_file(entry.name):
            try:
                size = entry.stat().st_size
            except OSError:
                size = 0
            files.append({
                "name": entry.name,
                "type": "file",
                "size_bytes": size,
                "path": rel_path,
            })

    return dirs + files


async def list_entries(subpath: str = "") -> list[dict]:
    """
    Lista diretórios e arquivos de vídeo (async wrapper).
    """
    return await asyncio.to_thread(_list_entries_sync, subpath)


def _list_video_files_sync(subpath: str) -> list[dict]:
    """Lista apenas os arquivos de vídeo em um subcaminho."""
    entries = _list_entries_sync(subpath)
    return [e for e in entries if e["type"] == "file"]


async def list_video_files(subpath: str = "") -> list[dict]:
    """Lista apenas os arquivos de vídeo (async wrapper)."""
    return await asyncio.to_thread(_list_video_files_sync, subpath)


def filename_to_title(filename: str) -> str:
    """
    Extrai um título limpo a partir do nome do arquivo.
    Exemplos:
      'aula_01-introducao.mp4' → 'aula 01 introducao'
      '03. Conceitos Básicos.mkv' → '03. Conceitos Básicos'
    """
    stem = Path(filename).stem
    # Substitui _ e - por espaço
    title = stem.replace("_", " ").replace("-", " ")
    # Remove espaços duplicados
    title = " ".join(title.split())
    return title
