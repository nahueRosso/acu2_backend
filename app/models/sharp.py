"""Modelo Sharp (Modelo 2).

Fórmulas tomadas de CLAUDE.md, sección "Fórmulas — fuente: AYUDA_TP1" (fuente
normativa de la cátedra para este TP). A diferencia de una primera versión
de este módulo (basada en material introductorio genérico), esta fórmula
no usa f11 ni requiere dimensiones de panel de referencia: depende sólo de
fc, m (masa superficial) y ηTOTAL(f).
"""

from __future__ import annotations

import math

from .bands import (
    RHO0,
    THIRD_OCTAVE_BANDS,
    C0,
    PanelParams,
    eta_total,
    frecuencia_critica,
    masa_superficial,
)


def _r_bajo(f: float, m: float) -> float:
    """R = 10·log10(1 + (π·m·f / (ρ0·c0))²) − 5.5   (f < 0.5·fc)"""
    return 10 * math.log10(1 + (math.pi * m * f / (RHO0 * C0)) ** 2) - 5.5


def _r_alto(f: float, m: float, fc: float, eta_tot: float) -> float:
    """f >= fc: R = mínimo(R1, R2), ver CLAUDE.md."""
    base = 10 * math.log10(1 + (math.pi * m * f / (RHO0 * C0)) ** 2)
    r1 = base + 10 * math.log10(2 * eta_tot * f / (math.pi * fc))
    r2 = base - 5.5
    return min(r1, r2)


def modelo_sharp(panel: PanelParams) -> list[float]:
    """Índice de reducción sonora R por tercio de octava según el modelo Sharp.

        f < 0.5·fc:        R = 10·log10(1 + (π·m·f/(ρ0·c0))²) − 5.5

        0.5·fc <= f < fc:  interpolación lineal (en dB, vs. f -- no vs.
                           log(f); validado contra tp1_casos_referencia.json,
                           interpolar en log(f) da errores de hasta ~1.3 dB)
                           entre el valor en f=0.5·fc (fórmula de arriba) y
                           el valor en f=fc (fórmula de abajo, evaluada en
                           f=fc)

        f >= fc:           R = mínimo(R1, R2), con R1 y R2 según CLAUDE.md
    """
    m = masa_superficial(panel)
    fc = frecuencia_critica(panel)

    resultado = []
    for f in THIRD_OCTAVE_BANDS:
        if f < 0.5 * fc:
            r = _r_bajo(f, m)
        elif f < fc:
            f_a, f_b = 0.5 * fc, fc
            r_a = _r_bajo(f_a, m)
            r_b = _r_alto(f_b, m, fc, eta_total(panel, f_b))
            t = (f - f_a) / (f_b - f_a)
            r = r_a + t * (r_b - r_a)
        else:
            r = _r_alto(f, m, fc, eta_total(panel, f))
        resultado.append(r)
    return resultado
