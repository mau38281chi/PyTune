"""Vista de la lista de canciones de la playlist activa (ttk.Treeview)."""
from __future__ import annotations

from collections.abc import Callable
from tkinter import ttk

import customtkinter as ctk

from src.config import COLOR_PLAYING, COLOR_ROW_ALT
from src.models import Track, format_duration


class TrackList(ctk.CTkFrame):
    """Tabla de pistas con resaltado de la cancion en reproduccion."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        on_activate: Callable[[int], None],
        on_remove: Callable[[int], None],
    ) -> None:
        super().__init__(master)
        self._on_activate = on_activate
        self._on_remove = on_remove
        self._tracks: list[Track] = []
        self._playing_index: int | None = None

        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=8, pady=(8, 0))
        self._title = ctk.CTkLabel(
            toolbar,
            text="Playlist",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self._title.pack(side="left")
        self._count = ctk.CTkLabel(toolbar, text="0 canciones", text_color="gray")
        self._count.pack(side="right")

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=8, pady=8)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:  # noqa: BLE001
            pass
        style.configure(
            "Track.Treeview",
            background="#242424",
            fieldbackground="#242424",
            foreground="#e6e6e6",
            rowheight=30,
            borderwidth=0,
        )
        style.map("Track.Treeview", background=[("selected", "#1f6aa5")])
        style.configure(
            "Track.Treeview.Heading",
            background="#2f2f2f",
            foreground="#e6e6e6",
            borderwidth=0,
        )

        columns = ("num", "title", "artist", "album", "duration")
        self._tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            style="Track.Treeview",
            selectmode="browse",
        )
        self._tree.heading("num", text="#")
        self._tree.heading("title", text="Titulo")
        self._tree.heading("artist", text="Artista")
        self._tree.heading("album", text="Album")
        self._tree.heading("duration", text="Duracion")
        self._tree.column("num", width=44, anchor="center", stretch=False)
        self._tree.column("title", width=280, anchor="w")
        self._tree.column("artist", width=200, anchor="w")
        self._tree.column("album", width=200, anchor="w")
        self._tree.column("duration", width=80, anchor="center", stretch=False)

        scrollbar = ctk.CTkScrollbar(container, command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._tree.tag_configure("playing", foreground=COLOR_PLAYING)
        self._tree.tag_configure("missing", foreground="#b46464")
        self._tree.tag_configure("odd", background=COLOR_ROW_ALT)
        self._tree.tag_configure("even", background="#242424")

        self._tree.bind("<Double-1>", self._handle_double_click)
        self._tree.bind("<Return>", self._handle_double_click)
        self._tree.bind("<Delete>", self._handle_delete)

    # -- render --------------------------------------------------------
    def set_playlist_name(self, name: str) -> None:
        self._title.configure(text=name)

    def set_tracks(self, tracks: list[Track]) -> None:
        self._tracks = tracks
        self._rebuild()

    def _rebuild(self) -> None:
        self._tree.delete(*self._tree.get_children())
        for index, track in enumerate(self._tracks):
            tags = ["odd" if index % 2 else "even"]
            if not track.exists:
                tags.append("missing")
            if self._playing_index == index:
                tags.append("playing")
            self._tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    index + 1,
                    track.display_title,
                    track.artist,
                    track.album,
                    format_duration(track.duration),
                ),
                tags=tuple(tags),
            )
        self._count.configure(text=f"{len(self._tracks)} canciones")
        if self._playing_index is not None and self._playing_index < len(self._tracks):
            self._apply_playing_tag(self._playing_index)

    def _apply_playing_tag(self, index: int) -> None:
        iid = str(index)
        if not self._tree.exists(iid):
            return
        base = list(self._tree.item(iid, "tags"))
        base = [t for t in base if t != "playing"]
        self._tree.item(iid, tags=tuple(base + ["playing"]))

    # -- resaltado cancion actual --------------------------------------
    def set_playing_index(self, index: int | None) -> None:
        previous = self._playing_index
        self._playing_index = index
        if previous is not None and self._tree.exists(str(previous)):
            tags = [t for t in self._tree.item(str(previous), "tags") if t != "playing"]
            self._tree.item(str(previous), tags=tuple(tags))
        if index is not None and self._tree.exists(str(index)):
            self._apply_playing_tag(index)
            self._tree.selection_set(str(index))
            self._tree.see(str(index))

    # -- eventos -------------------------------------------------------
    def _selected_index(self) -> int | None:
        selection = self._tree.selection()
        if not selection:
            return None
        return int(selection[0])

    def _handle_double_click(self, _event: object) -> None:
        index = self._selected_index()
        if index is not None:
            self._on_activate(index)

    def _handle_delete(self, _event: object) -> None:
        index = self._selected_index()
        if index is not None:
            self._on_remove(index)
