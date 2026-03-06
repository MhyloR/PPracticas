# ApiExportar_SinCSV.py
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, Dict, Tuple, List

import pandas as pd


# =============================================================================
# ERRORES
# =============================================================================
class ExportError(Exception):
    pass

class ValidationError(ExportError):
    pass


# =============================================================================
# UTILIDADES (no cambian)
# =============================================================================
class FilenameSanitizer:
    @staticmethod
    def sanitize(value: Any) -> str:
        if pd.isna(value):
            return "NaN"
        s = str(value).strip().replace(" ", "_")
        s = re.sub(r'[\\/:*?"<>|]+', "", s)
        s = re.sub(r"_+", "_", s)
        return s[:120] if len(s) > 120 else (s or "valor_vacio")


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class ExportRequest:
    df: pd.DataFrame
    columna: str
    valor_objetivo: Optional[Any] = None

    def validate(self):
        if not isinstance(self.df, pd.DataFrame):
            raise ValidationError("df debe ser un DataFrame válido.")
        if self.columna not in self.df.columns:
            raise ValidationError(
                f"La columna '{self.columna}' no existe. Columnas: {list(self.df.columns)}"
            )


@dataclass(frozen=True)
class ExportResult:
    resultados: Dict[str, int]    # etiqueta → conteo
    dataframe: pd.DataFrame       # subset o df original


# =============================================================================
# SERVICIO PRINCIPAL (SIN CSV)
# =============================================================================
class ColumnExporterService:
    """
    MISMO COMPORTAMIENTO, pero SIN generar archivos CSV.
    """
    def export(self, req: ExportRequest) -> ExportResult:
        req.validate()

        df = req.df
        serie = df[req.columna].astype("object")

        resultados: Dict[str, int] = {}

        # ----------------------------------------------------------------------
        # Caso 1: filtrar SOLO el valor objetivo
        # ----------------------------------------------------------------------
        if req.valor_objetivo is not None:
            subset, etiqueta = self._filtrar(serie, req.valor_objetivo, df)
            resultados[etiqueta] = len(subset)
            return ExportResult(resultados, subset)

        # ----------------------------------------------------------------------
        # Caso 2: exportar TODOS los valores
        # ----------------------------------------------------------------------
        valores_unicos = serie.drop_duplicates(keep="first")

        if serie.isna().any() and not valores_unicos.isna().any():
            valores_unicos = pd.concat(
                [valores_unicos, pd.Series([float("nan")])],
                ignore_index=True
            )

        for valor in valores_unicos:
            subset, etiqueta = self._filtrar(serie, valor, df)
            if subset.empty:
                continue
            resultados[etiqueta] = len(subset)

        return ExportResult(resultados, df)

    # ----------------------------------------------------------------------
    # Helper interno
    # ----------------------------------------------------------------------
    def _filtrar(self, serie: pd.Series, valor: Any, df: pd.DataFrame):
        if pd.isna(valor):
            mascara = serie.isna()
            etiqueta = "NaN"
        else:
            mascara = serie == valor
            etiqueta = str(valor)
        return df.loc[mascara], etiqueta


# =============================================================================
# API COMPATIBLE (MISMA FIRMA, SIN CSV)
# =============================================================================
def exportar_por_columna(
    df: pd.DataFrame,
    columna: str,
    valor_objetivo: Optional[Any] = None,
) -> Tuple[Dict[str, int], pd.DataFrame]:
    """
    MISMA API, MISMA SALIDA
    PERO YA NO SE GENERA NINGÚN ARCHIVO CSV.
    """
    service = ColumnExporterService()
    result = service.export(
        ExportRequest(df=df, columna=columna, valor_objetivo=valor_objetivo)
    )
    return result.resultados, result.dataframe


# =============================================================================
# MODO INTERACTIVO (SE MANTIENE IGUAL)
# =============================================================================
def _elegir_columna_interactivo(df: pd.DataFrame) -> str:
    columnas = list(df.columns)
    print("\nColumnas disponibles:")
    for i, c in enumerate(columnas, start=1):
        print(f"  {i}. {c}")

    entrada = input("\nElige la columna (número o nombre exacto): ").strip()

    if entrada.isdigit():
        idx = int(entrada)
        if 1 <= idx <= len(columnas):
            return columnas[idx - 1]
        raise ValueError("Índice fuera de rango.")

    if entrada in df.columns:
        return entrada

    raise KeyError(f"La columna '{entrada}' no existe.")


def _elegir_valor_interactivo(serie: pd.Series) -> Any:
    serie_obj = serie.astype("object")

    valores = serie_obj.drop_duplicates(keep="first")
    if serie_obj.isna().any() and not valores.isna().any():
        valores = pd.concat([valores, pd.Series([float("nan")])], ignore_index=True)

    print("\nValores disponibles:")
    for i, v in enumerate(valores, start=1):
        print(f"{i}. {v}")

    entrada = input("\nElige valor (número o texto exacto): ").strip()

    if entrada.isdigit():
        idx = int(entrada)
        return valores.iloc[idx - 1]

    return entrada


def ejecutar_interactivo(df: pd.DataFrame):
    """
    MISMA FUNCIÓN DEL CÓDIGO ORIGINAL,
    PERO YA NO GENERA CSV — SOLO MUESTRA RESULTADOS.
    """
    print("=== Exportar por valor de columna (NO se generarán CSV) ===")

    columna = _elegir_columna_interactivo(df)
    print(f"\nColumna seleccionada: {columna}")

    valor = _elegir_valor_interactivo(df[columna])

    resultados, subset = exportar_por_columna(
        df=df,
        columna=columna,
        valor_objetivo=valor,
    )

    print("\nResultados generados (solo en memoria):")
    for etiqueta, filas in resultados.items():
        print(f"  {etiqueta} → {filas} filas")

    return subset
