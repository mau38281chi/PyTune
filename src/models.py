"""Modelos de datos tipados para pistas y playlists."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass(slots=True)
class Track:
    """Representa una pista de audio local con sus metadatos."""

    path: str
    title: str = ""
    artist: str = "Artista desconocido"
    album: str = ""
    duration: float = 0.0
    cover_path: str | None = None

    @property
    def display_title(self) -> str:
        return self.title or Path(self.path).stem

    @property
    def exists(self) -> bool:
        return Path(self.path).is_file()

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "duration": self.duration,
            "cover_path": self.cover_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Track":
        return cls(
            path=str(data.get("path", "")),
            title=str(data.get("title", "")),
            artist=str(data.get("artist", "Artista desconocido")),
            album=str(data.get("album", "")),
            duration=float(data.get("duration", 0.0)),
            cover_path=data.get("cover_path"),
        )


@dataclass(slots=True)
class Playlist:
    """Lista de reproduccion con identificador estable."""

    name: str
    tracks: list[Track] = field(default_factory=list)
    id: str = field(default_factory=_new_id)

    def add_track(self, track: Track) -> None:
        self.tracks.append(track)

    def add_tracks(self, tracks: list[Track]) -> int:
        """Agrega pistas evitando duplicados por ruta. Devuelve cuantas se anadieron."""
        existing = {t.path for t in self.tracks}
        added = 0
        for track in tracks:
            if track.path not in existing:
                self.tracks.append(track)
                existing.add(track.path)
                added += 1
        return added

    def remove_track(self, track: Track) -> bool:
        for index, current in enumerate(self.tracks):
            if current.path == track.path:
                del self.tracks[index]
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tracks": [t.to_dict() for t in self.tracks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Playlist":
        return cls(
            name=str(data.get("name", "Playlist")),
            tracks=[Track.from_dict(t) for t in data.get("tracks", [])],
            id=str(data.get("id") or _new_id()),
        )


def format_duration(seconds: float) -> str:
    """Convierte segundos a formato mm:ss o h:mm:ss."""
    if seconds is None or seconds < 0:
        seconds = 0
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"
