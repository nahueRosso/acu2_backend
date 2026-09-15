"""Modelo ISO 12354-1 / UNE-EN 12354-1:2000, Anexo B (Modelo 4).

Fórmula principal (B.1) tomada de CLAUDE.md, sección "Fórmulas — fuente:
AYUDA_TP1". Los factores de radiación σ (ondas libres) y σf (transmisión
forzada) NO están completos en CLAUDE.md: dependen de f11, fc, dimensiones
del panel y del número de onda k0=2πf/c0, con varios casos (σ1, σ2, σ3
según f11 vs fc/2), y la norma tiene copyright (AENOR) por lo que su
desarrollo completo no fue transcripto.

PENDIENTE (bloqueante para poder calcular R con este modelo): conseguir el
desarrollo completo de σ y σf del Anexo B (CLAUDE.md sugiere pedírselo a
Claude vía chat, no a Claude Code, y pegar el resultado en CLAUDE.md) y
completar `_factor_radiacion_ondas_libres` / `_factor_radiacion_forzada`
abajo. No inventar ni aproximar estas fórmulas mientras tanto.

NOTA ADICIONAL: CLAUDE.md tampoco define numéricamente qué ancho de banda
cuenta como "f ≈ fc" (la rama del medio de la fórmula B.1). Se usa acá un
±5% de tolerancia relativa (`math.isclose(f, fc, rel_tol=0.05)`) sólo para
que la función tenga una rama que tomar; es un criterio propio, no un dato
de CLAUDE.md - confirmarlo con la cátedra junto con σ/σf.
"""

from __future__ import annotations

import math

from .bands import (
    C0,
    RHO0,
    THIRD_OCTAVE_BANDS,
    PanelParams,
    eta_total,
    frecuencia_critica,
    masa_superficial,
)


def _factor_radiacion_ondas_libres(panel: PanelParams, f: float, fc: float) -> float:
    """σ: factor de radiación para ondas libres (Anexo B, UNE-EN 12354-1).

    PENDIENTE: depende de f11, fc, dimensiones del panel y k0=2πf/c0, con
    distintos casos según f11 <= fc/2 o no. Ver docstring del módulo.
    """
    raise NotImplementedError(
        "Factor de radiación σ (ondas libres) pendiente: falta el desarrollo "
        "completo del Anexo B de UNE-EN 12354-1 (no transcripto en CLAUDE.md "
        "por tratarse de una norma con copyright)."
    )


def _factor_radiacion_forzada(panel: PanelParams, f: float, fc: float) -> float:
    """σf: factor de radiación para transmisión forzada (Anexo B, UNE-EN 12354-1).

    PENDIENTE: mismo motivo que _factor_radiacion_ondas_libres.
    """
    raise NotImplementedError(
        "Factor de radiación σf (transmisión forzada) pendiente: falta el "
        "desarrollo completo del Anexo B de UNE-EN 12354-1 (no transcripto "
        "en CLAUDE.md por tratarse de una norma con copyright)."
    )


def modelo_iso12354(panel: PanelParams) -> list[float]:
    """Índice de reducción sonora R por tercio de octava según ISO 12354-1 (Anexo B).

        τ = factor de transmisión ; R = −10·log10(τ)

        f > fc:   τ = (2·ρ0·c0 / (2π·f·m))² · (π·f·σ² / (2·ηTOTAL))
        f ≈ fc:   τ = (2·ρ0·c0 / (2π·f·m))² · (π·σf² / (2·ηTOTAL))
        f < fc:   τ = (2·ρ0·c0 / (2π·f·m))² ·
                      ((2σ²·l1·l2/(l1²+l2²)) + (6/π)·(fc/f)·(σ²/ηTOTAL))

    Todavía no calcula nada: σ y σf (ver funciones placeholder de este
    módulo) están pendientes de confirmar con la cátedra.
    """
    if panel.lx is None or panel.ly is None:
        raise ValueError("El modelo ISO 12354-1 requiere las dimensiones del panel (lx, ly)")

    m = masa_superficial(panel)
    fc = frecuencia_critica(panel)
    l1, l2 = panel.lx, panel.ly

    resultado = []
    for f in THIRD_OCTAVE_BANDS:
        eta_tot = eta_total(panel, f)
        base = (2 * RHO0 * C0 / (2 * math.pi * f * m)) ** 2

        if math.isclose(f, fc, rel_tol=0.05):
            sigma_f = _factor_radiacion_forzada(panel, f, fc)
            tau = base * (math.pi * sigma_f ** 2 / (2 * eta_tot))
        elif f > fc:
            sigma = _factor_radiacion_ondas_libres(panel, f, fc)
            tau = base * (math.pi * f * sigma ** 2 / (2 * eta_tot))
        else:
            sigma = _factor_radiacion_ondas_libres(panel, f, fc)
            tau = base * (
                (2 * sigma ** 2 * l1 * l2 / (l1 ** 2 + l2 ** 2))
                + (6 / math.pi) * (fc / f) * (sigma ** 2 / eta_tot)
            )

        resultado.append(-10 * math.log10(tau))
    return resultado
