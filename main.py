"""Punto de entrada del reproductor de musica PyTune."""
from __future__ import annotations

import logging
import sys

from src.config import ensure_directories
from src.ui.app import build_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> int:
    ensure_directories()
    try:
        app = build_app()
    except SystemExit as exc:
        return int(exc.code or 0)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
