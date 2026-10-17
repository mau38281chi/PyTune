"""Ventana principal y orquestacion entre UI, motor de audio y almacenamiento."""
from __future__ import annotations

import logging
import random
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.audio.engine import AudioEngine, VlcNotAvailableError
from src.config import (
    APP_NAME,
    APPEARANCE_MODE,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_THEME,
    SEEK_TICK_MS,
    SUPPORTED_EXTENSIONS,
    VOLUME_DEFAULT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from src.data.metadata import read_metadata
from src.data.storage import PlaylistRepository
from src.models import Playlist
from src.ui.controls import ControlsPanel
from src.ui.sidebar import Sidebar
from src.ui.tracklist import TrackList

logger = logging.getLogger(__name__)


class MusicPlayerApp(ctk.CTk):
    """Aplicacion principal."""

    def __init__(self, engine: AudioEngine) -> None:
        super().__init__()
        self.engine = engine
        self.repository = PlaylistRepository()

        self.playlists: list[Playlist] = self.repository.load()
        self._ensure_default_playlist()
        self.active_id: str = self.playlists[0].id
        self.current_index: int | None = None
        self.shuffle: bool = False
        self.loop: bool = False
        self._history: list[int] = []

        self.title(f"{APP_NAME} - Reproductor de musica")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.geometry(f"{WINDOW_MIN_WIDTH}x{WINDOW_MIN_HEIGHT}")
        self._build_layout()
        self._wire_engine()
        self.refresh_all()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # -- construccion de layout ---------------------------------------
    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            self,
            on_select=self.select_playlist,
            on_create=self.create_playlist,
            on_delete=self.delete_playlist,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")

        main = ctk.CTkFrame(self, corner_radius=0)
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(0, weight=1)

        self.tracklist = TrackList(
            main,
            on_activate=self.play_index,
            on_remove=self.remove_track,
        )
        self.tracklist.grid(row=0, column=0, sticky="nsew")

        toolbar = ctk.CTkFrame(main, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=8)
        ctk.CTkButton(
            toolbar,
            text="+ Agregar canciones",
            command=self.add_tracks,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
        ).pack(side="left", padx=(0, 8))
        ctk.CTkButton(
            toolbar,
            text="Quitar seleccionada",
            command=lambda: self.remove_track(self._selected_index()),
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
        ).pack(side="left")

        self.controls = ControlsPanel(
            main,
            on_play_pause=self.toggle_play_pause,
            on_stop=self.stop,
            on_next=self.next_track,
            on_prev=self.prev_track,
            on_seek=self.seek,
            on_volume=self.set_volume,
            on_toggle_shuffle=self.toggle_shuffle,
            on_toggle_loop=self.toggle_loop,
            on_toggle_mute=self.toggle_mute,
        )
        self.controls.grid(row=2, column=0, sticky="ew")

    def _wire_engine(self) -> None:
        self.engine.on_end(self._handle_track_end)
        self.engine.on_error(lambda msg: self.after(0, lambda: self._show_error(msg)))

    # -- helpers de estado ---------------------------------------------
    def _ensure_default_playlist(self) -> None:
        if not self.playlists:
            from src.config import DEFAULT_PLAYLIST_NAME

            self.playlists = [Playlist(name=DEFAULT_PLAYLIST_NAME)]
            self.repository.save(self.playlists)

    def active_playlist(self) -> Playlist:
        for playlist in self.playlists:
            if playlist.id == self.active_id:
                return playlist
        self.active_id = self.playlists[0].id
        return self.playlists[0]

    def _selected_index(self) -> int | None:
        selection = self.tracklist._tree.selection()
        return int(selection[0]) if selection else None

    # -- refresco de UI ------------------------------------------------
    def refresh_all(self) -> None:
        playlist = self.active_playlist()
        self.sidebar.render([(p.id, p.name) for p in self.playlists], self.active_id)
        self.tracklist.set_playlist_name(playlist.name)
        self.tracklist.set_tracks(playlist.tracks)
        self.tracklist.set_playing_index(self.current_index)

    def _persist(self) -> None:
        self.repository.save(self.playlists)

    # -- gestion de playlists ------------------------------------------
    def select_playlist(self, playlist_id: str) -> None:
        if playlist_id == self.active_id:
            return
        self.stop()
        self.active_id = playlist_id
        self.current_index = None
        self.refresh_all()

    def create_playlist(self) -> None:
        dialog = ctk.CTkInputDialog(text="Nombre de la nueva playlist:", title="Nueva playlist")
        name = dialog.get_input()
        if not name:
            return
        new_playlist = Playlist(name=name.strip())
        self.playlists.append(new_playlist)
        self.active_id = new_playlist.id
        self.current_index = None
        self._persist()
        self.refresh_all()

    def delete_playlist(self) -> None:
        if len(self.playlists) <= 1:
            messagebox.showinfo(APP_NAME, "Debe existir al menos una playlist.")
            return
        playlist = self.active_playlist()
        if not messagebox.askyesno(APP_NAME, f"Eliminar la playlist '{playlist.name}'?"):
            return
        self.stop()
        self.playlists = [p for p in self.playlists if p.id != playlist.id]
        self.active_id = self.playlists[0].id
        self.current_index = None
        self._persist()
        self.refresh_all()

    # -- gestion de canciones ------------------------------------------
    def add_tracks(self) -> None:
        patterns = " ".join(f"*{ext}" for ext in sorted(SUPPORTED_EXTENSIONS))
        paths = filedialog.askopenfilenames(
            title="Seleccionar archivos de audio",
            filetypes=[("Audio", patterns), ("Todos los archivos", "*.*")],
        )
        if not paths:
            return
        tracks = [read_metadata(p) for p in paths]
        added = self.active_playlist().add_tracks(tracks)
        self._persist()
        self.refresh_all()
        if added == 0:
            messagebox.showinfo(APP_NAME, "Las canciones ya estaban en la playlist.")

    def remove_track(self, index: int | None) -> None:
        if index is None:
            messagebox.showinfo(APP_NAME, "Selecciona una cancion para quitar.")
            return
        playlist = self.active_playlist()
        if not (0 <= index < len(playlist.tracks)):
            return
        removing_current = self.current_index == index
        playlist.remove_track(playlist.tracks[index])
        if removing_current:
            self.stop()
            self.current_index = None
        elif self.current_index is not None and index < self.current_index:
            self.current_index -= 1
        self._persist()
        self.refresh_all()

    # -- reproduccion --------------------------------------------------
    def play_index(self, index: int, *, autoplay: bool = True) -> None:
        playlist = self.active_playlist()
        if not (0 <= index < len(playlist.tracks)):
            return
        track = playlist.tracks[index]
        if not track.exists:
            self._show_error(f"El archivo no existe:\n{track.path}")
            return
        if not self.engine.load(track.path):
            self._show_error("No se pudo cargar el archivo.")
            return
        self.current_index = index
        if autoplay:
            self.engine.play()
            self._history.append(index)
        self.controls.set_now_playing(f"{track.display_title} - {track.artist}")
        if track.duration > 0:
            self.controls.update_progress(0, int(track.duration * 1000), force=True)
        self.tracklist.set_playing_index(index)
        self._update_play_icon()
        self._schedule_tick()

    def toggle_play_pause(self) -> None:
        if self.current_index is None:
            playlist = self.active_playlist()
            if playlist.tracks:
                self.play_index(0)
            return
        self.engine.toggle_pause()
        self._update_play_icon()

    def stop(self) -> None:
        self.engine.stop()
        self.current_index = None
        self.controls.set_now_playing("Sin reproduccion")
        self.controls.reset_progress()
        self.controls.set_play_icon(False)
        self.tracklist.set_playing_index(None)

    def next_track(self) -> None:
        playlist = self.active_playlist()
        if not playlist.tracks:
            return
        if self.current_index is None:
            self.play_index(0)
            return
        next_index = self._pick_next_index(len(playlist.tracks))
        self.play_index(next_index)

    def prev_track(self) -> None:
        playlist = self.active_playlist()
        if not playlist.tracks:
            return
        if self.current_index is None:
            self.play_index(0)
            return
        if self.shuffle and self._history:
            previous = self._history.pop()
            self.play_index(previous)
            return
        previous = (self.current_index - 1) % len(playlist.tracks)
        self.play_index(previous)

    def _pick_next_index(self, total: int) -> int:
        if self.shuffle:
            if total == 1:
                return 0
            choices = [i for i in range(total) if i != self.current_index]
            return random.choice(choices)
        return (self.current_index + 1) % total if self.current_index is not None else 0

    def _handle_track_end(self) -> None:
        self.after(0, self._advance_after_end)

    def _advance_after_end(self) -> None:
        playlist = self.active_playlist()
        total = len(playlist.tracks)
        if total == 0 or self.current_index is None:
            return
        if not self.loop and not self.shuffle and self.current_index == total - 1:
            self.stop()
            return
        self.next_track()

    def seek(self, fraction: float) -> None:
        self.engine.seek_fraction(fraction)

    def set_volume(self, value: int) -> None:
        self.engine.set_volume(value)

    def toggle_mute(self) -> bool:
        return self.engine.toggle_mute()

    def toggle_shuffle(self) -> None:
        self.shuffle = not self.shuffle
        self.controls.set_shuffle_active(self.shuffle)

    def toggle_loop(self) -> None:
        self.loop = not self.loop
        self.controls.set_loop_active(self.loop)

    # -- tick de progreso ----------------------------------------------
    def _schedule_tick(self) -> None:
        self.after(SEEK_TICK_MS, self._tick)

    def _tick(self) -> None:
        if self.current_index is None or not self.engine.is_playing():
            return
        current = self.engine.get_time_ms()
        total = self.engine.get_duration_ms()
        if total <= 0:
            playlist = self.active_playlist()
            if 0 <= self.current_index < len(playlist.tracks):
                total = int(playlist.tracks[self.current_index].duration * 1000)
        self.controls.update_progress(current, total)
        self._update_play_icon()
        self._schedule_tick()

    def _update_play_icon(self) -> None:
        self.controls.set_play_icon(self.engine.is_playing())

    # -- utilidades ----------------------------------------------------
    def _show_error(self, message: str) -> None:
        messagebox.showerror(APP_NAME, message)

    def _on_close(self) -> None:
        try:
            self._persist()
            self.engine.release()
        finally:
            self.destroy()


def build_app() -> MusicPlayerApp:
    """Fabrica la app, reportando un error claro si VLC no esta disponible."""
    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme(COLOR_THEME)
    try:
        engine = AudioEngine()
    except VlcNotAvailableError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, str(exc))
        root.destroy()
        raise SystemExit(1) from exc
    engine.set_volume(VOLUME_DEFAULT)
    return MusicPlayerApp(engine)
