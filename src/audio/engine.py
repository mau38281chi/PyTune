"""Motor de reproduccion basado en python-vlc."""
from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from src.config import VOLUME_DEFAULT, VOLUME_MAX

logger = logging.getLogger(__name__)


class VlcNotAvailableError(RuntimeError):
    """Se lanza cuando VLC no esta instalado o no puede inicializarse."""


class AudioEngine:
    """Wrapper sobre VLC que expone una API simple para la UI.

    La UI nunca debe llamar metodos de VLC directamente. Toda la interaccion
    pasa por esta clase y sus callbacks ``on_end`` / ``on_tick`` / ``on_error``.
    """

    def __init__(self) -> None:
        try:
            import vlc  # type: ignore
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise VlcNotAvailableError(
                "python-vlc no esta instalado. Ejecuta 'pip install python-vlc'."
            ) from exc

        self._vlc = vlc
        try:
            self._instance = vlc.Instance("--no-video", "--quiet")
        except Exception as exc:  # noqa: BLE001
            raise VlcNotAvailableError(
                "No se pudo inicializar VLC. Verifica que VLC este instalado y "
                "que libvlc sea accesible en PATH."
            ) from exc

        self._player = self._instance.media_player_new()
        self._media: object | None = None
        self._current_end_callback: Callable[[], None] | None = None
        self._duration_ms: int = 0
        self._on_end: Callable[[], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._muted: bool = False
        self._volume: int = VOLUME_DEFAULT
        self._bind_events()
        self.set_volume(VOLUME_DEFAULT)

    # -- configuracion de callbacks -------------------------------------
    def on_end(self, callback: Callable[[], None] | None) -> None:
        self._on_end = callback

    def on_error(self, callback: Callable[[str], None] | None) -> None:
        self._on_error = callback

    def _bind_events(self) -> None:
        events = self._vlc.EventType
        manager = self._player.event_manager()
        manager.event_attach(
            events.MediaPlayerEndReached,
            self._handle_end,
        )
        manager.event_attach(
            events.MediaPlayerEncounteredError,
            self._handle_error,
        )

    def _handle_end(self, _event: object) -> None:
        cb = self._on_end
        if cb is not None:
            cb()

    def _handle_error(self, _event: object) -> None:
        logger.warning("VLC encontro un error al reproducir.")
        cb = self._on_error
        if cb is not None:
            cb("Error de reproduccion en VLC.")

    # -- carga y control -----------------------------------------------
    def load(self, file_path: str) -> bool:
        """Carga un archivo local. Devuelve True si se pudo preparar."""
        if not Path(file_path).is_file():
            logger.warning("Archivo inexistente: %s", file_path)
            return False
        media = self._instance.media_new_path(str(Path(file_path).resolve()))
        if media is None:
            return False
        media.add_option("no-video")
        self._media = media
        self._player.set_media(media)
        self._duration_ms = 0
        return True

    def play(self) -> None:
        if self._player.play() == -1 and self._on_error is not None:
            self._on_error("No se pudo iniciar la reproduccion.")

    def pause(self) -> None:
        self._player.pause()

    def stop(self) -> None:
        self._player.stop()

    def toggle_pause(self) -> None:
        self._player.pause()

    def is_playing(self) -> bool:
        return bool(self._player.is_playing())

    def set_volume(self, value: int) -> None:
        """Ajusta el volumen (0-100)."""
        clamped = max(0, min(VOLUME_MAX, int(value)))
        self._volume = clamped
        self._player.audio_set_volume(clamped)

    def get_volume(self) -> int:
        return self._volume

    def set_mute(self, muted: bool) -> None:
        self._muted = muted
        self._player.audio_set_mute(muted)

    def toggle_mute(self) -> bool:
        self.set_mute(not self._muted)
        return self._muted

    def is_muted(self) -> bool:
        return self._muted

    # -- posicion / tiempo ---------------------------------------------
    def _total_ms(self) -> int:
        if self._duration_ms > 0:
            return self._duration_ms
        length = self._player.get_length()
        if length and length > 0:
            self._duration_ms = int(length)
        return self._duration_ms

    def get_time_ms(self) -> int:
        current = self._player.get_time()
        return int(current) if current and current > 0 else 0

    def get_duration_ms(self) -> int:
        return self._total_ms()

    def seek_fraction(self, fraction: float) -> None:
        total = self._total_ms()
        if total <= 0:
            return
        fraction = max(0.0, min(1.0, fraction))
        self._player.set_time(int(total * fraction))

    def position_fraction(self) -> float:
        total = self._total_ms()
        if total <= 0:
            return 0.0
        return min(1.0, self.get_time_ms() / total)

    def release(self) -> None:
        try:
            self._player.stop()
            self._player.release()
            self._instance.release()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Error al liberar VLC: %s", exc)
