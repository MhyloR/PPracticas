# ApiExportar_SinCSV.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Any, Dict, Tuple

import pandas as pd


# =============================================================================
# ERRORS
# =============================================================================
class ExportError(Exception):
    """Base error for export-related failures."""
    pass

class ValidationError(ExportError):
    """Raised when preconditions/inputs are invalid."""
    pass


# =============================================================================
# UTILITIES (unchanged behavior)
# =============================================================================
class FilenameSanitizer:
    @staticmethod
    def sanitize(value: Any) -> str:
        """
        Produce a filesystem-friendly token from any value.
        Rules:
        - NaN -> "NaN"
        - Trim, replace spaces with underscores
        - Remove characters forbidden in typical filesystems: \ / : * ? " < > |
        - Collapse multiple underscores
        - Limit to 120 chars
        - Fallback to "valor_vacio" if empty after cleaning
        Note: Kept as-is to preserve original logic even if we don't write CSVs.
        """
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
    """
    Input for the column-based export (in-memory).
    df: Source DataFrame
    columna: Column to use for filtering/splitting
    valor_objetivo: If provided, only that value is filtered; otherwise all distinct values are processed
    """
    df: pd.DataFrame
    columna: str
    valor_objetivo: Optional[Any] = None

    def validate(self) -> None:
        """Guard against invalid DataFrame or missing column."""
        if not isinstance(self.df, pd.DataFrame):
            raise ValidationError("df must be a valid pandas DataFrame.")
        if self.columna not in self.df.columns:
            raise ValidationError(
                f"Column '{self.columna}' does not exist. Columns: {list(self.df.columns)}"
            )


@dataclass(frozen=True)
class ExportResult:
    """
    Output of the in-memory export.
    resultados: Mapping label -> row count for each processed value
    dataframe: If valor_objetivo is set, this is the subset; otherwise, the original df
    """
    resultados: Dict[str, int]    # label → count
    dataframe: pd.DataFrame       # subset or original df


# =============================================================================
# MAIN SERVICE (NO CSV)
# =============================================================================
class ColumnExporterService:
    """
    Same observable behavior as the original export logic,
    but it DOES NOT create CSV files anymore—everything stays in memory.
    """
    def export(self, req: ExportRequest) -> ExportResult:
        # 1) Validate inputs
        req.validate()

        df = req.df
        # Work on a Series coerced to object to preserve mixed types and NaN handling.
        serie = df[req.columna].astype("object")

        resultados: Dict[str, int] = {}

        # Precompute distinct values, ensuring NaN is included if present in the series
        valores_unicos = serie.drop_duplicates(keep="first")
        if serie.isna().any() and not valores_unicos.isna().any():
            valores_unicos = pd.concat(
                [valores_unicos, pd.Series([float("nan")])],
                ignore_index=True
            )

        # ----------------------------------------------------------------------
        # Case 1: filter ONLY the target value (must be one of the available options)
        # ----------------------------------------------------------------------
        if req.valor_objetivo is not None:
            if not self._valor_en_opciones(req.valor_objetivo, valores_unicos):
                opciones_legibles = [self._etiqueta_de_valor(v) for v in valores_unicos]
                raise ValidationError(
                    f"Provided value is not among available options. "
                    f"value={self._etiqueta_de_valor(req.valor_objetivo)} | options={opciones_legibles}"
                )
            subset, etiqueta = self._filtrar(serie, req.valor_objetivo, df)
            resultados[etiqueta] = len(subset)
            # Return only the subset (matching original semantics when a target is provided)
            return ExportResult(resultados, subset)

        # ----------------------------------------------------------------------
        # Case 2: process ALL distinct values in the column
        # ----------------------------------------------------------------------
        # Build counts for each unique value; keep only non-empty subsets
        for valor in valores_unicos:
            subset, etiqueta = self._filtrar(serie, valor, df)
            if subset.empty:
                continue
            resultados[etiqueta] = len(subset)

        # For the "all values" mode, return the original df alongside the counts
        return ExportResult(resultados, df)

    # ----------------------------------------------------------------------
    # Internal helper: returns (subset_df, label)
    # ----------------------------------------------------------------------
    def _filtrar(self, serie: pd.Series, valor: Any, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        """
        Create a boolean mask for the given value and return the filtered DataFrame plus a label.
        NaN requires special handling (isna) because NaN != NaN.
        """
        if pd.isna(valor):
            mascara = serie.isna()
            etiqueta = "NaN"
        else:
            mascara = serie == valor
            etiqueta = str(valor)
        return df.loc[mascara], etiqueta

    def _valor_en_opciones(self, valor: Any, opciones: pd.Series) -> bool:
        """
        Check if 'valor' is one of the allowed options (including NaN semantics).
        """
        if pd.isna(valor):
            return opciones.isna().any()
        # Compare by equality; for objects/strings should work as expected
        try:
            return any((~opciones.isna()) & (opciones == valor))
        except Exception:
            # Fallback: string comparison if native equality fails for complex types
            return any(str(v) == str(valor) for v in opciones.tolist())

    @staticmethod
    def _etiqueta_de_valor(valor: Any) -> str:
        """Consistent human-readable label, treating NaN distinctly."""
        return "NaN" if pd.isna(valor) else str(valor)


# =============================================================================
# COMPATIBLE API (SAME SIGNATURE, NO CSV)
# =============================================================================
def exportar_por_columna(
    df: pd.DataFrame,
    columna: str,
    valor_objetivo: Optional[Any] = None,
) -> Tuple[Dict[str, int], pd.DataFrame]:
    """
    Same API and same return shape as the original function,
    BUT it no longer writes any CSV files.
    Returns:
      (results: dict[label -> count], dataframe: subset or original)
    """
    service = ColumnExporterService()
    result = service.export(
        ExportRequest(df=df, columna=columna, valor_objetivo=valor_objetivo)
    )
    return result.resultados, result.dataframe


# =============================================================================
# INTERACTIVE MODE (strict validation of user input)
# =============================================================================
def _elegir_columna_interactivo(df: pd.DataFrame) -> str:
    """
    Show available columns and force the user to choose either:
    - A valid numeric index in range [1..N], or
    - An exact column name present in the DataFrame.
    Keeps prompting until a valid input is provided.
    """
    columnas = list(df.columns)
    while True:
        print("\nAvailable columns:")
        for i, c in enumerate(columnas, start=1):
            print(f"  {i}. {c}")

        entrada = input("\nChoose column (number or exact name): ").strip()

        # Numeric selection with 1-based index
        if entrada.isdigit():
            idx = int(entrada)
            if 1 <= idx <= len(columnas):
                return columnas[idx - 1]
            print(f"Error: index out of range (1..{len(columnas)}). Please try again.")
            continue

        # Exact name match
        if entrada in df.columns:
            return entrada

        print(f"Error: column '{entrada}' does not exist. Please choose a valid option.")


def _elegir_valor_interactivo(serie: pd.Series) -> Any:
    """
    List distinct values (including NaN if present) and force the user to select:
    - A valid numeric index within the shown range, or
    - An exact textual value that matches one of the shown options (including 'NaN').
    Keeps prompting until a valid input is provided.
    """
    serie_obj = serie.astype("object")

    valores = serie_obj.drop_duplicates(keep="first")
    # Explicitly include NaN as a selectable option if present in the series
    if serie_obj.isna().any() and not valores.isna().any():
        valores = pd.concat([valores, pd.Series([float("nan")])], ignore_index=True)

    # Precompute human-readable labels (strings), mapping to actual values
    opciones: list[tuple[str, Any]] = []
    for v in valores:
        etiqueta = "NaN" if pd.isna(v) else str(v)
        opciones.append((etiqueta, v))

    while True:
        print("\nAvailable values:")
        for i, (etiqueta, _) in enumerate(opciones, start=1):
            print(f"{i}. {etiqueta}")

        entrada = input("\nChoose value (number in list or exact text): ").strip()

        # Case 1: number in range
        if entrada.isdigit():
            idx = int(entrada)
            if 1 <= idx <= len(opciones):
                return opciones[idx - 1][1]
            print(f"Error: index out of range (1..{len(opciones)}). Please try again.")
            continue

        # Case 2: exact textual match to one of the shown labels
        matches = [v for (etiqueta, v) in opciones if etiqueta == entrada]
        if matches:
            return matches[0]

        print("Error: value not in the available options. Please select a valid number or exact text.")


def ejecutar_interactivo(df: pd.DataFrame) -> pd.DataFrame:
    """
    Same interactive function as the original code,
    but NO CSVs are generated—only in-memory results are shown.
    Now enforces that the selection is one of the displayed options.
    Returns the subset DataFrame that matches the chosen value.
    """
    print("=== Export by column value (NO CSV will be generated) ===")

    columna = _elegir_columna_interactivo(df)
    print(f"\nSelected column: {columna}")

    valor = _elegir_valor_interactivo(df[columna])

    resultados, subset = exportar_por_columna(
        df=df,
        columna=columna,
        valor_objetivo=valor,
    )

    print("\nGenerated results (in-memory only):")
    for etiqueta, filas in resultados.items():
        print(f"  {etiqueta} → {filas} rows")

    return subset