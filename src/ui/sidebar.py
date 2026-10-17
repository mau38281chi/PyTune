"""Panel lateral con la lista de playlists y acciones CRUD."""
from __future__ import annotations

from collections.abc import Callable

import customtkinter as ctk

from src.config import COLOR_ACCENT, COLOR_ACCENT_HOVER


class Sidebar(ctk.CTkFrame):
    """Lista de playlists y botones para crear/eliminar."""

    def __init__(
        self,
        master: ctk.CTk,
        *,
        on_select: Callable[[str], None],
        on_create: Callable[[], None],
        on_delete: Callable[[], None],
    ) -> None:
        super().__init__(master, width=220, corner_radius=0)
        self._on_select = on_select
        self._on_delete = on_delete
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._active_id: str | None = None

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="Playlists",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left")

        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=8, pady=4)

        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(4, 16))

        ctk.CTkButton(
            actions,
            text="+ Nueva",
            command=on_create,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
        ).pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            actions,
            text="Eliminar",
            command=on_delete,
            fg_color="#3a3a3a",
            hover_color="#4a4a4a",
        ).pack(fill="x")

    def render(self, playlists: list[tuple[str, str]], active_id: str | None) -> None:
        """Recibe lista de (id, nombre) y reconstruye los botones."""
        self._active_id = active_id
        for button in self._buttons.values():
            button.destroy()
        self._buttons.clear()

        for playlist_id, name in playlists:
            active = playlist_id == active_id
            button = ctk.CTkButton(
                self._list_frame,
                text=name,
                anchor="w",
                fg_color=COLOR_ACCENT if active else "transparent",
                hover_color=COLOR_ACCENT_HOVER if active else "#333333",
                command=lambda pid=playlist_id: self._on_select(pid),
            )
            button.pack(fill="x", pady=2)
            self._buttons[playlist_id] = button

    def get_active_id(self) -> str | None:
        return self._active_id
