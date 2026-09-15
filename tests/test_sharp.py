"""Valida modelo_sharp contra los 5 casos reales resueltos por la cátedra
(tp1_casos_referencia.json), banda por banda, tolerancia ±0.5 dB. Reemplaza
el sanity check genérico de pendiente por una validación numérica real."""

import pytest

from app.models.sharp import modelo_sharp
from tests._ref_utils import (
    cargar_casos_referencia,
    cargar_materiales,
    construir_panel,
    diferencias_banda_a_banda,
    formatear_diferencias,
    obtener_r_esperado,
)

CASOS = cargar_casos_referencia()
MATERIALES = cargar_materiales()


@pytest.mark.parametrize("caso", CASOS, ids=[c["material"] for c in CASOS])
def test_sharp_contra_caso_referencia(caso):
    panel = construir_panel(caso, MATERIALES)
    esperado = obtener_r_esperado(caso, "SHARP")
    assert esperado is not None, f"No se encontró 'SHARP' en el caso {caso['material']}"

    obtenido = modelo_sharp(panel)

    diffs = diferencias_banda_a_banda(caso["frecuencias_Hz"], esperado, obtenido)
    assert not diffs, formatear_diferencias("Sharp", caso["material"], diffs)
