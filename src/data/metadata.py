"""Extraccion de metadatos y caratulas con mutagen."""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from mutagen import File as MutagenFile
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, ID3
from mutagen.mp4 import MP4Cover

from src.config import COVERS_DIR, ensure_directories
from src.models import Track

logger = logging.getLogger(__name__)


def _extract_cover_bytes(audio: object) -> tuple[bytes, str] | None:
    """Devuelve (bytes, extension) de la caratula embebida si existe."""
    try:
        if isinstance(audio, FLAC) and audio.pictures:
            pic: Picture = audio.pictures[0]
            return pic.data, _ext(pic.mime)

        tags = getattr(audio, "tags", None)
        if isinstance(tags, ID3):
            for tag in tags.getall("APIC"):
                return tag.data, _ext(tag.mime)

        if tags is not None and "covr" in tags:
            cover = tags["covr"][0]
            data = bytes(cover)
            ext = "png" if cover.imageformat == MP4Cover.FORMAT_PNG else "jpg"
            return data, ext
    except (AttributeError, IndexError, KeyError, ValueError) as exc:
        logger.debug("Sin caratula legible: %s", exc)
    return None


def _ext(mime: str | None) -> str:
    if mime and "png" in mime.lower():
        return "png"
    return "jpg"


def _save_cover(data: bytes, ext: str, source: Path) -> str | None:
    ensure_directories()
    digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:16]
    target = COVERS_DIR / f"{digest}.{ext}"
    try:
        if not target.is_file():
            target.write_bytes(data)
        return str(target)
    except OSError as exc:
        logger.debug("No se pudo guardar caratula: %s", exc)
        return None


def read_metadata(path: str | Path) -> Track:
    """Lee metadatos de un archivo de audio; cae a valores por defecto si falla."""
    file_path = Path(path)
    track = Track(path=str(file_path))
    try:
        audio = MutagenFile(file_path, easy=True)
    except Exception as exc:  # noqa: BLE001 - mutagen lanza varios tipos
        logger.warning("No se pudieron leer metadatos de %s: %s", file_path, exc)
        track.title = file_path.stem
        return track

    if audio is None:
        track.title = file_path.stem
        return track

    info = getattr(audio, "info", None)
    if info is not None:
        track.duration = float(getattr(info, "length", 0.0) or 0.0)

    tags = getattr(audio, "tags", None) or {}
    track.title = _first(tags, "title") or file_path.stem
    track.artist = _first(tags, "artist") or "Artista desconocido"
    track.album = _first(tags, "album") or ""

    raw_audio = MutagenFile(file_path)
    if raw_audio is not None:
        cover = _extract_cover_bytes(raw_audio)
        if cover is not None:
            track.cover_path = _save_cover(cover[0], cover[1], file_path)

    return track


def _first(tags: dict, key: str) -> str:
    value = tags.get(key)
    if not value:
        return ""
    if isinstance(value, list):
        return str(value[0])
    return str(value)
