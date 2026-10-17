"""Configuracion global, rutas y constantes de la aplicacion."""
from __future__ import annotations

from pathlib import Path

APP_NAME: str = "PyTune"
APP_VERSION: str = "1.0.0"

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
COVERS_DIR: Path = DATA_DIR / "covers"
PLAYLISTS_FILE: Path = DATA_DIR / "playlists.json"

SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
    {".mp3", ".wav", ".flac", ".ogg", ".opus", ".m4a", ".aac", ".wma"}
)

DEFAULT_PLAYLIST_NAME: str = "Mi musica"

APPEARANCE_MODE: str = "dark"
COLOR_THEME: str = "blue"

WINDOW_MIN_WIDTH: int = 1024
WINDOW_MIN_HEIGHT: int = 640

SEEK_TICK_MS: int = 500
VOLUME_DEFAULT: int = 70
VOLUME_MAX: int = 100

COLOR_ACCENT: str = "#1f6aa5"
COLOR_ACCENT_HOVER: str = "#17527d"
COLOR_PLAYING: str = "#2fa572"
COLOR_ROW_ALT: str = "#2a2a2a"


def ensure_directories() -> None:
    """Crea los directorios de datos si no existen."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COVERS_DIR.mkdir(parents=True, exist_ok=True)
