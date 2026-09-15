"""Bandas de tercio de octava (20 Hz - 20 kHz) y propiedades físicas comunes del panel.

Fórmulas y constantes tomadas de la fuente normativa del TP1 ("AYUDA_TP1",
ver CLAUDE.md sección "Fórmulas — fuente: AYUDA_TP1"), no de las
diapositivas de clase. Este módulo centraliza lo que usan todos los
modelos de predicción (mass_law, sharp, iso12354, davy) para evitar
duplicar fórmulas de m, B, fc, fd y ηTOTAL.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

# Velocidad del sonido en aire [m/s]
C0 = 343.0

# Densidad del aire [kg/m³] (AYUDA_TP1 usa 1.18, no el 1.2 habitual)
RHO0 = 1.18

# Bandas normalizadas de tercio de octava, 20 Hz a 20 kHz (ISO 266), 31 bandas.
THIRD_OCTAVE_BANDS: list[float] = [
    20, 25, 31.5, 40, 50, 63, 80, 100, 125, 160,
    200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600,
    2000, 2500, 3150, 4000, 5000, 6300, 8000, 10000, 12500, 16000,
    20000,
]

# Razón entre el borde de banda y la frecuencia central de un tercio de octava.
_THIRD_OCTAVE_EDGE_RATIO = 2 ** (1 / 6)


def band_edges(f_center: float) -> tuple[float, float]:
    """Devuelve (f_inferior, f_superior) de la banda de tercio de octava centrada en f_center."""
    return f_center / _THIRD_OCTAVE_EDGE_RATIO, f_center * _THIRD_OCTAVE_EDGE_RATIO


@dataclass
class PanelParams:
    """Parámetros físicos de entrada de un panel simple homogéneo.

    Atributos:
        espesor: espesor del panel t (o l/h) [m]
        densidad: densidad volumétrica ρ [kg/m³]
        modulo_young: módulo de Young E [Pa]
        poisson: coeficiente de Poisson σ [-]
        factor_perdidas: factor de pérdidas INTERNO ηINTERNO [-] (no confundir
            con ηTOTAL, que depende de la frecuencia — ver eta_total())
        lx, ly: dimensiones del panel [m] (l1/l2 en la nomenclatura de
            AYUDA_TP1; requeridas por Davy, y por ISO 12354-1 para los
            factores de radiación σ/σf)
    """

    espesor: float
    densidad: float
    modulo_young: float
    poisson: float
    factor_perdidas: float
    lx: Optional[float] = None
    ly: Optional[float] = None


def masa_superficial(panel: PanelParams) -> float:
    """m = ρ · t   [kg/m²]"""
    return panel.densidad * panel.espesor


def rigidez_flexion(panel: PanelParams) -> float:
    """Rigidez a flexión: B = E·t³ / (12·(1-σ²))   [N·m]"""
    t = panel.espesor
    return (panel.modulo_young * t ** 3) / (12 * (1 - panel.poisson ** 2))


def frecuencia_critica(panel: PanelParams) -> float:
    """fc = (c0² / 2π) · √(m/B)   [Hz]"""
    m = masa_superficial(panel)
    b = rigidez_flexion(panel)
    return (C0 ** 2 / (2 * math.pi)) * math.sqrt(m / b)


def frecuencia_densidad(panel: PanelParams) -> float:
    """fd = (E / (2π·ρ)) · √(m/B)   [Hz]"""
    m = masa_superficial(panel)
    b = rigidez_flexion(panel)
    return (panel.modulo_young / (2 * math.pi * panel.densidad)) * math.sqrt(m / b)


def frecuencia_f11(panel: PanelParams) -> float:
    """f11 = (c0² / (4·fc)) · (1/lx² + 1/ly²)   [Hz]  (modo (1,1) del panel finito)

    Requiere lx, ly (dimensiones del panel).
    """
    if panel.lx is None or panel.ly is None:
        raise ValueError("f11 requiere las dimensiones del panel (lx, ly)")
    fc = frecuencia_critica(panel)
    return (C0 ** 2 / (4 * fc)) * (1 / panel.lx ** 2 + 1 / panel.ly ** 2)


def eta_total(panel: PanelParams, f: float) -> float:
    """ηTOTAL(f) = ηINTERNO + m / (485·√f)   [-]

    A diferencia de η_INTERNO (constante del material), ηTOTAL depende de
    la frecuencia y de la masa superficial del panel.
    """
    m = masa_superficial(panel)
    return panel.factor_perdidas + m / (485 * math.sqrt(f))
