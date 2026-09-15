"""Lectura de la base de materiales oficial (backend/app/data/tp1_materiales.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "tp1_materiales.json"


@lru_cache(maxsize=1)
def cargar_materiales() -> list[dict]:
    with open(_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)
