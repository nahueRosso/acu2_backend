"""Ley de masas y ley de masas corregida (Modelo 1 - Teórico/Cremer, 3 zonas).

Fórmulas tomadas de CLAUDE.md, sección "Fórmulas — fuente: AYUDA_TP1" (fuente
normativa de la cátedra para este TP), no de las diapositivas de clase.
"""

from __future__ import annotations

import math

from .bands import (
    THIRD_OCTAVE_BANDS,
    PanelParams,
    eta_total,
    frecuencia_critica,
    frecuencia_densidad,
    masa_superficial,
)


def r_ley_de_masas(f: float, m: float) -> float:
    """R = 20·log10(m·f) − 47   [dB]  (incidencia difusa)"""
    return 20 * math.log10(m * f) - 47


def ley_de_masas(panel: PanelParams) -> list[float]:
    """Ley de masas simple para las bandas de tercio de octava 20 Hz-20 kHz.

    Válida en general para f < fc, pero se calcula en todo el rango para
    poder graficarla como referencia comparativa frente a la corregida.
    """
    m = masa_superficial(panel)
    return [r_ley_de_masas(f, m) for f in THIRD_OCTAVE_BANDS]


def ley_de_masas_corregida(panel: PanelParams) -> list[float]:
    """Modelo 1 (Teórico/Cremer): ley de masas corregida en 3 zonas.

        f < fc:            R = 20·log10(m·f) − 47

        fc < f < fd:       R = 20·log10(m·f) − 10·log10(π / (4·ηTOTAL))
                               − 10·log10(fc / (f − fc)) − 47

        f > fd:            R = 20·log10(m·f) − 47

    NOTA DE IMPLEMENTACIÓN 1: la fórmula de Zona II transcripta en CLAUDE.md
    incluye además un término "+ 10·log10(f/fc)". Validando contra los 5
    casos de referencia de tp1_casos_referencia.json (backend/app/data/),
    incluir ese término produce un error creciente con f (hasta +19.9 dB en
    el caso de Hormigón) que coincide exactamente, banda por banda, con
    10·log10(f/fc) — es decir, el término está de más. Sin él, el error
    contra los 5 casos de referencia baja a <0.01 dB. Se lo quitó acá;
    avisar a la cátedra por si el documento fuente tiene esa errata.

    NOTA DE IMPLEMENTACIÓN 2: la fórmula de Zona II tiene una singularidad
    matemática exactamente en f = fc (el término fc/(f−fc) diverge). Como
    CLAUDE.md no asigna explícitamente el punto f = fc a ninguna zona
    ("f < fc" y "fc < f < fd" son ambas estrictas), se lo incluye en la
    Zona I (f <= fc) para evitar la división por cero, que de otra forma
    ocurriría exactamente en el límite entre zonas.
    """
    m = masa_superficial(panel)
    fc = frecuencia_critica(panel)
    fd = frecuencia_densidad(panel)

    resultado = []
    for f in THIRD_OCTAVE_BANDS:
        if f <= fc:
            r = r_ley_de_masas(f, m)
        elif f < fd:
            eta_tot = eta_total(panel, f)
            r = (
                20 * math.log10(m * f)
                - 10 * math.log10(math.pi / (4 * eta_tot))
                - 10 * math.log10(fc / (f - fc))
                - 47
            )
        else:
            r = r_ley_de_masas(f, m)
        resultado.append(r)
    return resultado
