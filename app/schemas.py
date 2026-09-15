"""Modelos Pydantic de entrada/salida de la API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PanelInput(BaseModel):
    """Parámetros físicos de entrada del panel (ver CLAUDE.md - Datos de entrada)."""

    nombre_material: Optional[str] = Field(default=None, description="Nombre/etiqueta del material")
    espesor: float = Field(gt=0, description="Espesor l (o h) [m]")
    densidad: float = Field(gt=0, description="Densidad volumétrica ρ [kg/m³]")
    modulo_young: float = Field(gt=0, description="Módulo de Young E [Pa]")
    poisson: float = Field(ge=0, lt=0.5, description="Coeficiente de Poisson σ [-]")
    factor_perdidas: float = Field(
        gt=0,
        description="Factor de pérdidas INTERNO ηINTERNO [-] (ηTOTAL se deriva por banda, ver bands.eta_total)",
    )
    lx: Optional[float] = Field(default=None, gt=0, description="Dimensión Lx del panel [m]")
    ly: Optional[float] = Field(default=None, gt=0, description="Dimensión Ly del panel [m]")


class ResultadosModelos(BaseModel):
    """R [dB] por banda para cada modelo. None si el modelo aún no está implementado."""

    ley_de_masas: Optional[list[float]] = None
    ley_de_masas_corregida: Optional[list[float]] = None
    iso12354: Optional[list[float]] = None
    sharp: Optional[list[float]] = None
    davy: Optional[list[float]] = None


class CalculoResponse(BaseModel):
    frecuencias: list[float]
    resultados: ResultadosModelos
    entrada: PanelInput
