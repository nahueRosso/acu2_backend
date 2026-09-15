"""Modelo Davy (1990) (Modelo 3).

Traducción literal del pseudocódigo de CLAUDE.md, sección "Fórmulas — fuente:
AYUDA_TP1" (a su vez traducido de AYUDA_TP1_MODELO_DAVY.pdf). Se preserva la
estructura y nombres de variables del original (incluyendo el orden
largo/ancho tal como aparece en las llamadas, ver notas puntuales abajo) para
poder auditar la traducción línea a línea contra la fuente si hace falta.

Nota: el documento original usa `c` en algunas fórmulas donde correspondería
`c0` (probable error de tipeo de la cátedra) - se usa siempre C0 = 343 m/s,
como indica CLAUDE.md.
"""

from __future__ import annotations

import math

from .bands import C0, RHO0, THIRD_OCTAVE_BANDS, PanelParams

_COS2L_MAX = 0.9
_AVERAGES = 3  # promedio definido por Davy, sólo aplica a bandas de 1/3 de octava


def _sigma(g: float, f: float, ancho: float, largo: float) -> float:
    """Eficiencia de radiación. S y U son simétricos en ancho/largo, por lo
    que el orden de los argumentos posicionales no afecta el resultado."""
    w = 1.3
    beta = 0.234
    n = 2
    s = largo * ancho
    u = 2 * (largo + ancho)
    twoa = 4 * s / u
    k = 2 * math.pi * f / C0
    f_ = min(1, w * math.sqrt(math.pi / (k * twoa)))
    h = 1 / (math.sqrt(k * twoa / math.pi) * (2 / 3) - beta)
    q = 2 * math.pi / (k ** 2 * s)
    qn = q ** n

    if g < f_:
        xn = (h - (h / f_ - 1) * g) ** n
    else:
        xn = g ** n

    return (xn + qn) ** (-1 / n)


def _shear(f: float, rho: float, e: float, sigma: float, t: float) -> float:
    """Corrección por ondas de cortadura (deformación por corte)."""
    omega = 2 * math.pi * f
    chi = ((1 + sigma) / (0.87 + 1.12 * sigma)) ** 2
    x = t ** 2 / 12
    qp = e / (1 - sigma ** 2)
    c_ = -(omega ** 2)
    b_ = c_ * (1 + 2 * chi / (1 - sigma)) * x
    a_ = x * qp / rho

    kbcor2 = (-b_ + math.sqrt(b_ ** 2 - 4 * a_ * c_)) / (2 * a_)
    kb2 = math.sqrt(-c_ / a_)
    g_mod = e / (2 * (1 + sigma))
    kt2 = -c_ * rho * chi / g_mod
    kl2 = -c_ * rho / qp
    ks2 = kt2 + kl2

    asi = (1 + x * (kbcor2 * kt2 / kl2 - kt2)) ** 2
    bsi = 1 - x * kt2 + kbcor2 * ks2 / (kb2 ** 2)
    csi = math.sqrt(1 - x * kt2 + ks2 ** 2 / (4 * kb2 ** 2))

    return asi / (bsi * csi)


def _single_leaf_davy(
    f: float, rho: float, e: float, sigma: float, t: float, eta: float, largo: float, ancho: float
) -> float:
    """TL de un panel simple (sin promediar) a una única frecuencia f."""
    m = rho * t
    fc = math.sqrt(12 * rho * (1 - sigma ** 2) / e) * C0 ** 2 / (2 * math.pi * t)

    normal = RHO0 * C0 / (math.pi * f * m)
    normal2 = normal ** 2

    e_ = 2 * largo * ancho / (largo + ancho)
    cos2l = min(C0 / (2 * math.pi * f * e_), _COS2L_MAX)

    tau1 = normal2 * math.log((normal2 + 1) / (normal2 + cos2l))

    ratio = f / fc
    r = max(0.0, 1 - 1 / ratio)
    g = math.sqrt(r)

    rad = _sigma(g, f, largo, ancho)
    rad2 = rad ** 2

    netatotal = eta + rad * normal
    z = 2 / netatotal
    y = math.atan(z) - math.atan(z * (1 - ratio))

    tau2 = normal2 * rad2 * y / (netatotal * 2 * ratio)
    tau2 = tau2 * _shear(f, rho, e, sigma, t)

    tau = (tau1 + tau2) if f < fc else tau2

    return -10 * math.log10(tau)


def modelo_davy(panel: PanelParams) -> list[float]:
    """Índice de reducción sonora R por tercio de octava según el modelo Davy (1990).

    Requiere las dimensiones del panel (lx, ly) para el cálculo de la
    eficiencia de radiación.
    """
    if panel.lx is None or panel.ly is None:
        raise ValueError("El modelo Davy requiere las dimensiones del panel (lx, ly)")

    rho = panel.densidad
    e = panel.modulo_young
    sigma = panel.poisson
    t = panel.espesor
    eta_interno = panel.factor_perdidas
    l1, l2 = panel.lx, panel.ly

    m = rho * t
    b = (e / (1 - sigma ** 2)) * (t ** 3 / 12)
    fc = (C0 ** 2 / (2 * math.pi)) * math.sqrt(m / b)

    limit = 2 ** (1 / (2 * 3))

    resultado = []
    for f in THIRD_OCTAVE_BANDS:
        ntot = eta_interno + m / (485 * math.sqrt(f))
        ratio = f / fc

        if ratio < 1 / limit or ratio > limit:
            tl = _single_leaf_davy(f, rho, e, sigma, t, ntot, l2, l1)
        else:
            suma = 0.0
            for j in range(1, _AVERAGES + 1):
                factor = 2 ** ((2 * j - 1 - _AVERAGES) / (2 * _AVERAGES * 3))
                suma += 10 ** (-_single_leaf_davy(f * factor, rho, e, sigma, t, ntot, l2, l1) / 10)
            tl = -10 * math.log10(suma / _AVERAGES)

        resultado.append(tl)
    return resultado
