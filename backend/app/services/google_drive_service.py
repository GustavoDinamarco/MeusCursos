# app/services/google_drive_service.py
"""
Serviço de integração com o Google Drive API v3.

Responsabilidades:
- Parsear o folder ID a partir de URLs do Drive
- Listar os arquivos de vídeo de uma pasta pública
"""
import re

import httpx

DRIVE_API = "https://www.googleapis.com/drive/v3/files"
# Máximo de páginas a buscar (100 arquivos/página = 200 aulas no máximo)
MAX_PAGES = 2


def parse_folder_id(url: str) -> str:
    """
    Extrai o folder ID de uma URL do Google Drive.

    Formatos suportados:
      https://drive.google.com/drive/folders/{folderId}
      https://drive.google.com/drive/u/0/folders/{folderId}
      https://drive.google.com/drive/u/1/folders/{folderId}?usp=sharing
    """
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(
            "URL do Google Drive inválida. "
            "Use uma URL de pasta no formato: "
            "https://drive.google.com/drive/folders/{folderId}"
        )
    return match.group(1)


async def list_folder_videos(folder_id: str, api_key: str) -> list[dict]:
    """
    Lista todos os arquivos de vídeo de uma pasta pública do Drive.

    Retorna lista de dicts com {id, name} ordenados por nome.
    Faz paginação automática (até MAX_PAGES páginas de 100 arquivos).

    Levanta ValueError se a pasta estiver inacessível ou não existir.
    """
    results: list[dict] = []
    page_token: str | None = None

    async with httpx.AsyncClient(timeout=15.0) as client:
        for _ in range(MAX_PAGES):
            params: dict = {
                "q": f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false",
                "fields": "nextPageToken,files(id,name)",
                "orderBy": "name",
                "pageSize": 100,
                "key": api_key,
            }
            if page_token:
                params["pageToken"] = page_token

            response = await client.get(DRIVE_API, params=params)

            if response.status_code == 400:
                raise ValueError(
                    "Pasta do Google Drive inválida. Verifique o ID da pasta."
                )
            if response.status_code in (401, 403):
                raise PermissionError(
                    "Pasta do Drive inacessível. "
                    "Certifique-se de que está compartilhada como "
                    "'Qualquer pessoa com o link pode ver'."
                )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Erro ao acessar o Google Drive API: HTTP {response.status_code}"
                )

            data = response.json()
            files = data.get("files", [])
            results.extend({"id": f["id"], "name": f["name"]} for f in files)

            page_token = data.get("nextPageToken")
            if not page_token:
                break

    return results
