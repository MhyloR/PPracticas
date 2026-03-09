# ApiSeparacion.py
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple, Optional
import pandas as pd

# =============================================================================
# LOGGING (optional)
# =============================================================================
def setup_logging(level: int | str = logging.INFO) -> None:
    """
    Configure root logger only once.
    This avoids duplicate handlers if the module is imported multiple times.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )

log = logging.getLogger(__name__)


# =============================================================================
# ERRORS
# =============================================================================
class SeparacionError(Exception):
    """Base error for separation use case."""


class ValidationError(SeparacionError):
    """Raised when inputs are invalid."""


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class SeparacionRequest:
    """
    Input DTO for the separation flow.

    archivo: Source DataFrame.
    Note: In the original behavior, the `columnas` parameter is NOT used to
    select columns; instead, we validate real columns directly from the DataFrame.
    """
    archivo: pd.DataFrame
    # Note: selecting and renaming are interactive; they are not passed here.

    def validate(self) -> None:
        """Ensure the DataFrame is present and non-empty."""
        if not isinstance(self.archivo, pd.DataFrame):
            raise ValidationError(f"Expected a pandas DataFrame, got: {type(self.archivo)}")
        if self.archivo.empty:
            raise ValidationError("The DataFrame is empty.")


@dataclass(frozen=True)
class SeparacionResult:
    """
    Output DTO for the separation flow.

    df_general: Two-column DataFrame (X and Y) after optional renaming.
    df_atributos: Remaining columns from the original DataFrame.
    """
    df_general: pd.DataFrame
    df_atributos: pd.DataFrame


# =============================================================================
# COMPONENTS (single responsibilities)
# =============================================================================
class ColumnChooser:
    """
    Encapsulates interactive input to choose X and Y from existing DataFrame columns.

    This preserves the original console-driven behavior:
    - Prompts until a valid column name is provided.
    - Ensures Y != X.
    """

    def choose_x(self, valid_columns: list[str]) -> str:
        while True:
            var_x = input("X-axis variable: ").strip()
            if var_x in valid_columns:
                return var_x
            print(f"Column not found. Available: {valid_columns}")

    def choose_y(self, valid_columns: list[str], var_x: str) -> str:
        while True:
            var_y = input("Y-axis variable: ").strip()
            if var_y == var_x:
                print("Variable Y cannot be the same as X.")
                continue
            if var_y in valid_columns:
                return var_y
            print(f"Column not found. Available: {valid_columns}")


class TimeConverter:
    """
    Converts the X column to datetime replicating the original logic:
    1) Try strict format '%Y-%m-%d %H:%M:%S'
    2) If it fails, do a flexible parse with errors coerced to NaT
    """

    def to_datetime_like_original(self, df: pd.DataFrame, col_x: str) -> None:
        # First attempt: strict format
        try:
            df[col_x] = pd.to_datetime(df[col_x], format='%Y-%m-%d %H:%M:%S')
        except Exception:
            # Fallback: flexible parsing, coerce invalid strings to NaT
            df[col_x] = pd.to_datetime(df[col_x], errors='coerce', dayfirst=False)


class Renamer:
    """
    Handles interactive renaming ONLY for X and Y with validation.
    Keeps the interactive console prompts to match the original experience.
    """

    def interactive_rename_xy(self, var_x: str, var_y: str) -> tuple[str, str]:
        print("\n=== Rename columns in df_general (X and Y only) ===")
        print(f"Current X name: {var_x}")
        new_x = input("New name for X (Enter to keep): ").strip()
        if not new_x:
            new_x = var_x

        print(f"Current Y name: {var_y}")
        new_y = input("New name for Y (Enter to keep): ").strip()
        if not new_y:
            new_y = var_y

        self._validate_new_names(new_x, new_y)
        return new_x, new_y

    def _validate_new_names(self, new_x: str, new_y: str) -> None:
        """Simple guardrails to avoid empty or duplicate names."""
        if not new_x:
            raise ValidationError("Name for X cannot be empty.")
        if not new_y:
            raise ValidationError("Name for Y cannot be empty.")
        if new_x == new_y:
            raise ValidationError("X and Y names cannot be the same.")


# =============================================================================
# SERVICE (use case)
# =============================================================================
class SeparacionService:
    """
    Use case that reproduces the original behavior exactly:
    - Interactive selection of X and Y
    - df_general = archivo[[X, Y]].copy()
    - Convert X to datetime (strict first, then flexible/coerce)
    - df_atributos = archivo.drop([X, Y])
    - Interactive renaming of X and Y only
    """

    def __init__(
        self,
        chooser: Optional[ColumnChooser] = None,
        converter: Optional[TimeConverter] = None,
        renamer: Optional[Renamer] = None,
    ) -> None:
        self.chooser = chooser or ColumnChooser()
        self.converter = converter or TimeConverter()
        self.renamer = renamer or Renamer()

    def ejecutar(self, req: SeparacionRequest) -> SeparacionResult:
        """
        Orchestrate the full separation flow:
        1) Validate input
        2) Ask user for X and Y columns
        3) Build df_general (X, Y) and convert X to datetime
        4) Build df_atributos by dropping X and Y from the original
        5) Allow interactive renaming of X and Y
        6) Final sanity checks and return
        """
        req.validate()

        # Gather valid columns from the real DataFrame.
        valid_columns = list(req.archivo.columns)

        # Interactive selection of X and Y.
        var_x = self.chooser.choose_x(valid_columns)
        var_y = self.chooser.choose_y(valid_columns, var_x)

        # Build df_general and ensure X is datetime-like.
        df_general = req.archivo[[var_x, var_y]].copy()
        self.converter.to_datetime_like_original(df_general, var_x)

        # Remaining attributes: everything except X and Y.
        df_atributos = req.archivo.drop([var_x, var_y], axis=1).copy()

        # Interactive renaming of X and Y only.
        new_x, new_y = self.renamer.interactive_rename_xy(var_x, var_y)
        df_general.rename(columns={var_x: new_x, var_y: new_y}, inplace=True)

        # Final validations to match original logical guarantees.
        assert isinstance(df_general, pd.DataFrame), "df_general is not a DataFrame"
        assert isinstance(df_atributos, pd.DataFrame), "df_atributos is not a DataFrame"
        assert df_general.shape[1] == 2, f"df_general must have 2 columns, found {df_general.shape[1]}"

        return SeparacionResult(df_general=df_general, df_atributos=df_atributos)


# =============================================================================
# FACADE (compatibility with your original function)
# =============================================================================
def Separacion(columnas, archivo: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Facade with the SAME signature and observable behavior as the original function.
    It ignores 'columnas' for selection (as in the original), validating against the real DF.
    """
    service = SeparacionService()
    result = service.ejecutar(SeparacionRequest(archivo=archivo))
    return result.df_general, result.df_atributos