"""API FastAPI del TP1 - Aislamiento a ruido aéreo de panel simple."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .calculo import calcular_resultados
from .export.excel_export import generar_excel
from .models.bands import THIRD_OCTAVE_BANDS
from .schemas import CalculoResponse, PanelInput

app = FastAPI(title="TP1 - Aislamiento a ruido aéreo (panel simple)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/calcular", response_model=CalculoResponse)
def calcular(entrada: PanelInput) -> CalculoResponse:
    resultados = calcular_resultados(entrada)
    return CalculoResponse(
        frecuencias=THIRD_OCTAVE_BANDS,
        resultados=resultados,
        entrada=entrada,
    )


@app.post("/exportar-excel")
def exportar_excel(entrada: PanelInput) -> StreamingResponse:
    resultados = calcular_resultados(entrada)
    datos = CalculoResponse(
        frecuencias=THIRD_OCTAVE_BANDS,
        resultados=resultados,
        entrada=entrada,
    )
    buffer = generar_excel(datos)
    nombre_archivo = f"aislamiento_{entrada.nombre_material or 'panel'}.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
