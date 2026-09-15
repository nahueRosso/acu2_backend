"""Valida modelo_davy contra los 5 casos reales resueltos por la cátedra
(tp1_casos_referencia.json), banda por banda, tolerancia ±0.5 dB."""

import pytest

from app.models.davy import modelo_davy
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
def test_davy_contra_caso_referencia(caso):
    panel = construir_panel(caso, MATERIALES)
    esperado = obtener_r_esperado(caso, "DAVY")
    assert esperado is not None, f"No se encontró 'DAVY' en el caso {caso['material']}"

    obtenido = modelo_davy(panel)

    diffs = diferencias_banda_a_banda(caso["frecuencias_Hz"], esperado, obtenido)
    assert not diffs, formatear_diferencias("Davy", caso["material"], diffs)
