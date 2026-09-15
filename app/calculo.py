"""Orquesta el cálculo de R por banda para los 4 modelos a partir de un PanelInput."""

from __future__ import annotations

from .models.bands import PanelParams
from .models.davy import modelo_davy
from .models.iso12354 import modelo_iso12354
from .models.mass_law import ley_de_masas, ley_de_masas_corregida
from .models.sharp import modelo_sharp
from .schemas import PanelInput, ResultadosModelos


def _a_panel_params(entrada: PanelInput) -> PanelParams:
    return PanelParams(
        espesor=entrada.espesor,
        densidad=entrada.densidad,
        modulo_young=entrada.modulo_young,
        poisson=entrada.poisson,
        factor_perdidas=entrada.factor_perdidas,
        lx=entrada.lx,
        ly=entrada.ly,
    )


def calcular_resultados(entrada: PanelInput) -> ResultadosModelos:
    """Corre los 4 modelos; los que todavía no están implementados quedan en None."""
    panel = _a_panel_params(entrada)

    def _intentar(func):
        try:
            return func(panel)
        except NotImplementedError:
            # Modelo todavía no implementado (iso12354, ver docstring).
            return None
        except ValueError:
            # Modelo implementado pero requiere datos que no vinieron en la
            # entrada (p. ej. lx/ly para Davy/ISO 12354-1).
            return None

    return ResultadosModelos(
        ley_de_masas=_intentar(ley_de_masas),
        ley_de_masas_corregida=_intentar(ley_de_masas_corregida),
        sharp=_intentar(modelo_sharp),
        iso12354=_intentar(modelo_iso12354),
        davy=_intentar(modelo_davy),
    )
