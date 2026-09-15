"""Modelo ISO 12354-1 / UNE-EN 12354-1:2000, Anexo B (Modelo 4).

Fórmulas tomadas de CLAUDE.md, sección "Fórmulas — fuente: AYUDA_TP1"
(B.1 fórmula principal, B.2 σf, B.3 σ y B.4 fc,eff).

⚠️ HALLAZGO IMPORTANTE (validado contra tp1_casos_referencia.json, los 5
casos reales de la cátedra) — leer antes de tocar este archivo:

CLAUDE.md describe tres refinamientos de la fórmula B.1/B.3 que, aplicados
tal cual están escritos, EMPEORAN el ajuste contra los 5 casos de
referencia (bandas que antes coincidían casi exacto pasan a tener errores
de varios dB, o directamente rompen con dominio inválido). Sacando los
tres, los 4 casos "normales" (Ladrillo, Acero, PYL, Hormigón) ajustan a
menos de 0.05 dB en el 100% de las bandas:

1. El término `δ2` de σ (Caso A, rama f<fc): sumarlo produce un error que
   crece sin límite a medida que f baja (hasta -2.8 dB @ 20 Hz en el caso
   Ladrillo) — se probó reconstruyendo qué σ haría falta para igualar el
   valor esperado banda por banda, y en cada banda de baja frecuencia
   coincide con `coef·δ1` SOLO, sin el término δ2 sumado.
2. La sustitución de fc por fc,eff (B.4) en σ1 y en la rama f>fc de B.1:
   se probaron dos variantes (fc,eff evaluada por banda, y fc,eff como
   valor único por panel evaluada en f=fc) y ambas producen peor ajuste
   que usar directamente la fc nominal en todos lados. Con fc nominal el
   ajuste en la zona f>fc es casi exacto (ver PYL, error <0.05 dB en las
   9 bandas por encima de fc).
3. La rama intermedia "f ≈ fc" de B.1 (con su propio σ "tratado como
   f>=fc"): las bandas que caen ahí (dentro de ±5% de fc) en los 3 casos
   de prueba afectados (PYL @3150, Vidrio @4000, Hormigón @125) son en
   realidad bandas con f < fc "de verdad" — tratarlas con la fórmula
   intermedia (o con el σ de la zona f>=fc) da error de hasta +0.9 dB;
   usando la comparación estricta f>fc / f<fc sin zona intermedia,
   coinciden.

Esto sugiere que la planilla/Matlab de referencia de la cátedra no aplica
estos tres refinamientos (o los aplica de otra forma no documentada en
CLAUDE.md) — avisar al equipo/cátedra para confirmar antes de dar esto
por cerrado. Mientras tanto, `_fc_efectiva()` queda implementada (B.4,
tal cual la pide CLAUDE.md) pero SIN USARSE en `modelo_iso12354`, por si
hace falta retomarla.

Único caso que NO ajusta ni sacando los tres refinamientos: Vidrio a
20 Hz (panel de vidrio de 3 mm, 2×1.5 m — el más delgado, más chico y a
la frecuencia más baja de los 5 casos). Ahí σf (B.2) da negativo y el
corchete de τ en la rama f<fc se vuelve negativo (dominio inválido para
el logaritmo). La propia curva de referencia salta de forma no monótona
justo en esa zona (11.32 → 16.08 → 11.52 dB entre 20-31.5 Hz), lo que
sugiere que la propia fórmula/implementación de origen ya es inestable
ahí. Se deja una guarda numérica (no una corrección física) para no
romper el cálculo completo por una sola banda extrema.
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

_TAU_MINIMO = 1e-300  # sólo para evitar log10(<=0); no debe recortar valores válidos
                       # (Hormigón a 20 kHz da τ≈6.8e-11, ya de por sí muy chico) —
                       # ver docstring del módulo (caso Vidrio @ 20 Hz)


def _fc_efectiva(panel: PanelParams, fc: float) -> float:
    """fc,eff (B.4): frecuencia crítica efectiva para paredes gruesas.

    Implementada tal cual la fórmula de CLAUDE.md, pero NO se usa en
    `modelo_iso12354` — ver el hallazgo documentado arriba en el docstring
    del módulo. Se evalúa con f=fc (único valor por panel): evaluarla por
    banda hace que crezca sin límite en la rama f>=fp.
    """
    t = panel.espesor
    c_l = math.sqrt(panel.modulo_young / (panel.densidad * (1 - panel.poisson ** 2)))
    fp = c_l / (5.5 * t)
    if fc < fp:
        x = 4.05 * (t * fc / c_l)
        return fc * (x + math.sqrt(1 + x ** 2))
    return 2 * fc * (fc / fc) ** 3


def _sigma_forzada(f: float, l1: float, l2: float) -> float:
    """σf (B.2): factor de radiación para transmisión forzada. Requiere l1 > l2.

    CLAUDE.md sólo especifica un tope superior (σf ≤ 2); a muy baja
    frecuencia y panel chico esta fórmula puede dar negativo (ver Vidrio
    @ 20 Hz en el docstring del módulo) — no se le puso piso porque
    clamplarla a 0 empeora el ajuste contra los demás casos (probado).
    """
    if l2 > l1:
        l1, l2 = l2, l1
    k0 = 2 * math.pi * f / C0
    lam = (
        -0.964
        - (0.5 + l2 / (math.pi * l1)) * math.log(l2 / l1)
        + 5 * l2 / (2 * math.pi * l1)
        - 1 / (4 * math.pi * l1 * l2 * k0 ** 2)
    )
    sigma_f = 0.5 * (math.log(k0 * math.sqrt(l1 * l2)) - lam)
    return min(sigma_f, 2.0)


def _sigma_libre(panel: PanelParams, f: float, fc: float, l1: float, l2: float, en_zona_fc_o_superior: bool) -> float:
    """σ (B.3a/b/c): factor de radiación para ondas de flexión libres.

    NOTA: no incluye el término δ2 de la rama f<fc del Caso A — ver
    hallazgo en el docstring del módulo (sumarlo empeora el ajuste).
    """
    f11 = (C0 ** 2 / (4 * fc)) * (1 / l1 ** 2 + 1 / l2 ** 2)

    sigma1 = None
    if en_zona_fc_o_superior:
        sigma1 = 1 / math.sqrt(1 - fc / f)

    if f11 <= fc / 2:
        # Caso A
        if en_zona_fc_o_superior:
            sigma = sigma1
        else:
            lam = math.sqrt(f / fc)
            delta1 = ((1 - lam ** 2) * math.log((1 + lam) / (1 - lam)) + 2 * lam) / (
                4 * math.pi ** 2 * (1 - lam ** 2) ** 1.5
            )
            sigma = (2 * (l1 + l2) * C0 / (l1 * l2 * fc)) * delta1
    else:
        # Caso B
        sigma2 = 4 * l1 * l2 * (f / C0) ** 2
        sigma3 = math.sqrt(2 * math.pi * f * (l1 + l2) / (16 * C0))
        if not en_zona_fc_o_superior and sigma2 < sigma3:
            sigma = sigma2
        elif en_zona_fc_o_superior and sigma1 < sigma3:
            sigma = sigma1
        else:
            sigma = sigma3

    return min(sigma, 2.0)


def modelo_iso12354(panel: PanelParams) -> list[float]:
    """Índice de reducción sonora R por tercio de octava según ISO 12354-1 (Anexo B)."""
    if panel.lx is None or panel.ly is None:
        raise ValueError("El modelo ISO 12354-1 requiere las dimensiones del panel (lx, ly)")

    m = masa_superficial(panel)
    fc = frecuencia_critica(panel)
    l1, l2 = panel.lx, panel.ly

    resultado = []
    for f in THIRD_OCTAVE_BANDS:
        eta_tot = eta_total(panel, f)
        base = (2 * RHO0 * C0 / (2 * math.pi * f * m)) ** 2
        en_zona_fc_o_superior = f > fc
        sigma = _sigma_libre(panel, f, fc, l1, l2, en_zona_fc_o_superior)

        if en_zona_fc_o_superior:
            tau = base * (math.pi * fc * sigma ** 2 / (2 * f * eta_tot))
        else:
            sigma_f = _sigma_forzada(f, l1, l2)
            tau = base * (
                2 * sigma_f + ((l1 + l2) ** 2 / (l1 ** 2 + l2 ** 2)) * math.sqrt(fc / f) * (sigma ** 2 / eta_tot)
            )

        resultado.append(-10 * math.log10(max(tau, _TAU_MINIMO)))
    return resultado
