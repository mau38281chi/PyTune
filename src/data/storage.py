"""Repositorio de playlists con persistencia en JSON (escritura atomica)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path

from src.config import PLAYLISTS_FILE, ensure_directories
from src.models import Playlist

logger = logging.getLogger(__name__)


class PlaylistRepository:
    """Carga y guarda colecciones de playlists desde/hacia disco."""

    def __init__(self, file_path: Path = PLAYLISTS_FILE) -> None:
        self.file_path = file_path

    def load(self) -> list[Playlist]:
        """Devuelve las playlists almacenadas o una lista vacia si no hay datos."""
        ensure_directories()
        if not self.file_path.is_file():
            return []
        try:
            raw = self.file_path.read_text(encoding="utf-8")
            payload = json.loads(raw) if raw.strip() else {}
            raw_playlists = payload.get("playlists", [])
            return [Playlist.from_dict(item) for item in raw_playlists]
        except (json.JSONDecodeError, OSError, TypeError, AttributeError) as exc:
            logger.error("No se pudieron cargar las playlists: %s", exc)
            return []

    def save(self, playlists: list[Playlist]) -> None:
        """Guarda de forma atomica para evitar corrupcion del archivo."""
        ensure_directories()
        payload = {
            "version": 1,
            "playlists": [p.to_dict() for p in playlists],
        }
        directory = self.file_path.parent
        directory.mkdir(parents=True, exist_ok=True)
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".tmp",
                dir=directory,
                delete=False,
            ) as tmp:
                json.dump(payload, tmp, ensure_ascii=False, indent=2)
                temp_name = tmp.name
            os.replace(temp_name, self.file_path)
        except OSError as exc:
            logger.error("No se pudieron guardar las playlists: %s", exc)
