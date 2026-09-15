"""Utilidades compartidas para los tests de validación contra los casos de
referencia de la cátedra (backend/app/data/tp1_casos_referencia.json).

No es un módulo de test (no matchea test_*.py), pytest no lo colecciona.
"""

from __future__ import annotations

import json
from pathlib import Path

from app.models.bands import PanelParams

_DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"

TOLERANCIA_DB = 0.5


def cargar_casos_referencia() -> list[dict]:
    with open(_DATA_DIR / "tp1_casos_referencia.json", encoding="utf-8") as f:
        return json.load(f)


def cargar_materiales() -> dict[str, dict]:
    with open(_DATA_DIR / "tp1_materiales.json", encoding="utf-8") as f:
        materiales = json.load(f)
    return {m["material"]: m for m in materiales}


def construir_panel(caso: dict, materiales: dict[str, dict]) -> PanelParams:
    material = materiales[caso["material"]]
    return PanelParams(
        espesor=caso["espesor_m"],
        densidad=material["densidad_kg_m3"],
        modulo_young=material["modulo_young_Pa"],
        poisson=material["modulo_poisson"],
        factor_perdidas=material["factor_perdidas"],
        lx=caso["L1_m"],
        ly=caso["L2_m"],
    )


def obtener_r_esperado(caso: dict, clave_modelo: str) -> list[float] | None:
    """Busca la clave del modelo en R_por_modelo_dB, tolerando variantes de
    nombre (p. ej. "ISO 12354-1" vs "ISO 12354-1:2001")."""
    for clave, valores in caso["R_por_modelo_dB"].items():
        if clave.upper().startswith(clave_modelo.upper()):
            return valores
    return None


def diferencias_banda_a_banda(
    frecuencias: list[float],
    esperados: list[float],
    obtenidos: list[float],
    tolerancia: float = TOLERANCIA_DB,
) -> list[tuple[float, float, float, float]]:
    """Devuelve (frecuencia, esperado, obtenido, diferencia) sólo para las
    bandas donde |diferencia| > tolerancia."""
    fuera_de_tolerancia = []
    for f, esperado, obtenido in zip(frecuencias, esperados, obtenidos):
        diff = obtenido - esperado
        if abs(diff) > tolerancia:
            fuera_de_tolerancia.append((f, esperado, obtenido, diff))
    return fuera_de_tolerancia


def formatear_diferencias(nombre_modelo: str, material: str, diffs: list[tuple[float, float, float, float]]) -> str:
    lineas = [f"{nombre_modelo} / {material}: {len(diffs)} banda(s) fuera de ±{TOLERANCIA_DB} dB"]
    lineas.append(f"{'f (Hz)':>10} {'esperado':>10} {'obtenido':>10} {'diff':>8}")
    for f, esperado, obtenido, diff in diffs:
        lineas.append(f"{f:>10} {esperado:>10.2f} {obtenido:>10.2f} {diff:>+8.2f}")
    return "\n".join(lineas)
