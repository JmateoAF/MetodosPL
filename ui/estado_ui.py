"""Estado global de la UI.

Mantiene el problema activo compartido entre vistas sin tocar la capa `src/`.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

problema_activo: dict[str, Any] | None = None


def set_problema_activo(datos: dict[str, Any] | None) -> None:
    global problema_activo
    problema_activo = deepcopy(datos) if datos is not None else None


def get_problema_activo() -> dict[str, Any] | None:
    return deepcopy(problema_activo)
