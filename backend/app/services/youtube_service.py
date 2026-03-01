# app/services/youtube_service.py
"""
Serviço de importação de playlists do YouTube via yt-dlp.

Não requer Google API Key — usa a Innertube API interna do YouTube.
"""
import asyncio

import yt_dlp


async def list_playlist_videos(url: str) -> list[dict]:
    """
    Lista todos os vídeos de uma playlist pública do YouTube.

    Aceita qualquer URL reconhecida pelo yt-dlp:
      https://www.youtube.com/playlist?list={id}
      https://youtube.com/playlist?list={id}

    Retorna lista de dicts com {videoId, title} na ordem da playlist.
    Levanta ValueError se a URL for inválida ou inacessível.
    """

    def _extract() -> list[dict]:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            # Extrai apenas metadados — não baixa nada
            "extract_flat": "in_playlist",
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return []
                # Consome o gerador DENTRO do with para que o ydl ainda possa
                # paginar as próximas páginas da playlist enquanto está aberto.
                entries = info.get("entries") or []
                return [
                    {
                        "videoId": entry["id"],
                        "title": entry.get("title") or "Sem título",
                    }
                    for entry in entries
                    if entry and entry.get("id")
                ]
        except yt_dlp.utils.DownloadError as exc:
            raise ValueError(
                f"Não foi possível acessar a playlist: {exc}"
            ) from exc

    # yt-dlp é síncrono; executa em thread-pool para não bloquear o event loop
    return await asyncio.to_thread(_extract)
