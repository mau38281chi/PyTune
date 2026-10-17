"""Panel de control de reproduccion (play/pause/stop/next/prev, slider, volumen)."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.config import COLOR_ACCENT, COLOR_ACCENT_HOVER
from src.models import format_duration


class ControlsPanel(ctk.CTkFrame):
    """Barra inferior con controles de transporte y progreso."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        on_play_pause: Callable[[], None],
        on_stop: Callable[[], None],
        on_next: Callable[[], None],
        on_prev: Callable[[], None],
        on_seek: Callable[[float], None],
        on_volume: Callable[[int], None],
        on_toggle_shuffle: Callable[[], None],
        on_toggle_loop: Callable[[], None],
        on_toggle_mute: Callable[[], bool],
    ) -> None:
        super().__init__(master, corner_radius=0)
        self._on_seek = on_seek
        self._on_volume = on_volume
        self._on_toggle_mute = on_toggle_mute
        self._seeking = False

        self.grid_columnconfigure(1, weight=1)

        self._now_playing = ctk.CTkLabel(
            self,
            text="Sin reproduccion",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        )
        self._now_playing.grid(row=0, column=0, columnspan=6, sticky="ew", padx=16, pady=(10, 0))

        self._time_current = ctk.CTkLabel(self, text="00:00", width=48, anchor="e")
        self._time_current.grid(row=1, column=0, padx=(16, 4), pady=10)

        self._progress = ctk.CTkSlider(
            self,
            from_=0,
            to=1,
            command=self._on_slider_move,
        )
        self._progress.set(0)
        self._progress.grid(row=1, column=1, sticky="ew", padx=4, pady=10)
        self._progress.bind("<ButtonPress-1>", self._start_seek)
        self._progress.bind("<ButtonRelease-1>", self._end_seek)

        self._time_total = ctk.CTkLabel(self, text="00:00", width=48, anchor="w")
        self._time_total.grid(row=1, column=2, padx=4, pady=10)

        self._btn_prev = self._icon_button("\u23ee", on_prev)
        self._btn_prev.grid(row=1, column=3, padx=4)
        self._btn_play = self._icon_button("\u25b6", on_play_pause, accent=True)
        self._btn_play.grid(row=1, column=4, padx=4)
        self._btn_stop = self._icon_button("\u23f9", on_stop)
        self._btn_stop.grid(row=1, column=5, padx=4)
        self._btn_next = self._icon_button("\u23ed", on_next)
        self._btn_next.grid(row=1, column=6, padx=4)

        self._btn_shuffle = self._icon_button("\U0001f500", on_toggle_shuffle)
        self._btn_shuffle.grid(row=1, column=7, padx=(16, 4))
        self._btn_loop = self._icon_button("\U0001f501", on_toggle_loop)
        self._btn_loop.grid(row=1, column=8, padx=4)
        self._btn_mute = self._icon_button("\U0001f50a", self._handle_mute)
        self._btn_mute.grid(row=1, column=9, padx=(16, 4))

        self._volume = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            width=120,
            command=self._handle_volume,
        )
        self._volume.set(70)
        self._volume.grid(row=1, column=10, padx=(4, 16), pady=10)

        self._time_total.configure(text="00:00")

    def _icon_button(
        self,
        text: str,
        command: Callable[[], object],
        *,
        accent: bool = False,
    ) -> ctk.CTkButton:
        return ctk.CTkButton(
            self,
            text=text,
            width=44,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=16),
            command=command,
            fg_color=COLOR_ACCENT if accent else "#3a3a3a",
            hover_color=COLOR_ACCENT_HOVER if accent else "#4a4a4a",
        )

    # -- callbacks internos --------------------------------------------
    def _start_seek(self, _event: object) -> None:
        self._seeking = True

    def _end_seek(self, _event: object) -> None:
        self._seeking = False
        self._on_seek(float(self._progress.get()))

    def _on_slider_move(self, value: float) -> None:
        if self._seeking:
            return

    def _handle_volume(self, value: float) -> None:
        self._on_volume(int(value))

    def _handle_mute(self) -> None:
        muted = self._on_toggle_mute()
        self._btn_mute.configure(text="\U0001f507" if muted else "\U0001f50a")

    # -- API publica para la app ---------------------------------------
    def set_now_playing(self, text: str) -> None:
        self._now_playing.configure(text=text)

    def set_play_icon(self, playing: bool) -> None:
        self._btn_play.configure(text="\u23f8" if playing else "\u25b6")

    def update_progress(self, current_ms: int, total_ms: int, *, force: bool = False) -> None:
        if self._seeking and not force:
            return
        total = max(total_ms, 1)
        self._progress.set(min(1.0, current_ms / total))
        self._time_current.configure(text=format_duration(current_ms / 1000))
        self._time_total.configure(text=format_duration(total_ms / 1000))

    def reset_progress(self) -> None:
        self._progress.set(0)
        self._time_current.configure(text="00:00")
        self._time_total.configure(text="00:00")

    def set_shuffle_active(self, active: bool) -> None:
        self._btn_shuffle.configure(fg_color=COLOR_ACCENT if active else "#3a3a3a")

    def set_loop_active(self, active: bool) -> None:
        self._btn_loop.configure(fg_color=COLOR_ACCENT if active else "#3a3a3a")
