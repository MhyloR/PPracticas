# ApiColumns.py
from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

import pandas as pd


# =============================================================================
# LOGGING
# =============================================================================
def setup_logging(level: int | str = logging.INFO) -> None:
    """
    Configure a basic logging setup only if no handlers exist yet.
    This avoids duplicate handlers when the module is imported multiple times.
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
class AppError(Exception):
    """Base class for application-specific errors."""

class ValidationError(AppError):
    """Raised when inputs are invalid or inconsistent."""

class FileReadError(AppError):
    """Raised on file read errors."""

class TempWriteError(AppError):
    """Raised on temporary file creation/write errors."""


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class DataFrameColumnsRequest:
    """
    Request DTO to extract column names from a pandas DataFrame.
    """
    df: pd.DataFrame

    def validate(self) -> None:
        """
        Ensure the DataFrame is a valid pandas object and not None.
        """
        if self.df is None or not isinstance(self.df, pd.DataFrame):
            raise ValidationError("DataFrame cannot be None and must be a pandas DataFrame")


@dataclass(frozen=True)
class FileColumnsRequest:
    """
    Request DTO to extract header/column names from a delimited text file.

    path: path to a flat file (CSV/TSV/TXT)
    sep: expected delimiter; if None, pandas will attempt to infer it
         using sep=None with engine='python'
    crear_temp: if True, a temporary file with only the header row will be created
    """
    path: Path | str
    sep: Optional[str] = ","
    crear_temp: bool = False

    def validate(self) -> None:
        """
        Validate that the path exists and the separator (if provided) is a string.
        """
        p = Path(self.path)
        if not p.exists():
            raise ValidationError(f"File not found: {p}")
        if self.sep is not None and not isinstance(self.sep, str):
            raise ValidationError("sep must be a string or None")


@dataclass(frozen=True)
class FileColumnsResult:
    """
    Result DTO for file header extraction.

    columnas: list of column names (as strings)
    ruta_temp: absolute path to a generated temporary CSV containing only headers (if created), else None
    """
    columnas: List[str]
    ruta_temp: Optional[str] = None


# =============================================================================
# PORTS / INTERFACES
# =============================================================================
class HeaderReader:
    """
    Port for reading only the header/column names from a tabular file.
    Implementations should avoid loading full data to minimize memory and time.
    """
    def read_columns(self, path: Path, sep: Optional[str]) -> List[str]:
        raise NotImplementedError


class TempHeaderWriter:
    """
    Port for writing a temporary file that contains only the header row.
    """
    def write_header_temp(self, columnas: List[str]) -> str:
        raise NotImplementedError


# =============================================================================
# INFRASTRUCTURE (concrete adapters)
# =============================================================================
class PandasHeaderReader(HeaderReader):
    """
    Reads just the headers using pandas. Optimization: nrows=0 prevents loading data rows.
    When sep is None, allow delimiter inference via sep=None and engine='python'.
    """
    def read_columns(self, path: Path, sep: Optional[str]) -> List[str]:
        try:
            if sep is None:
                # Use python engine to enable delimiter inference with sep=None
                df = pd.read_csv(path, sep=None, engine="python", nrows=0)
            else:
                df = pd.read_csv(path, sep=sep, nrows=0)
            # Ensure all column labels are returned as strings
            return list(map(str, df.columns.tolist()))
        except FileNotFoundError as e:
            raise FileReadError(f"File not found: {path}") from e
        except Exception as e:
            # This can include parse errors, encoding issues, malformed CSV, etc.
            raise FileReadError(f"Failed to read headers from {path}: {e}") from e


class LocalTempHeaderWriter(TempHeaderWriter):
    """
    Creates a temporary .csv file that contains only the header row.
    Uses pandas to ensure quoting/escaping behavior is consistent.
    """
    def write_header_temp(self, columnas: List[str]) -> str:
        try:
            tmp = tempfile.NamedTemporaryFile(prefix="cols_", suffix=".csv", delete=False)
            # Write a zero-row DataFrame so resulting CSV has only the header line
            pd.DataFrame(columns=columnas).head(0).to_csv(tmp.name, index=False)
            tmp.close()
            return tmp.name
        except Exception as e:
            raise TempWriteError(f"Could not create temporary header file: {e}") from e


# =============================================================================
# SERVICE (use case)
# =============================================================================
class ColumnsService:
    """
    High-level use case for extracting column names from DataFrames or files.

    - obtener_columnas_df: returns column names from a DataFrame (validated, with logging).
    - obtener_columnas_archivo: returns column names from a file using HeaderReader and,
      optionally, creates a CSV temp file with only the header via TempHeaderWriter.
    """
    def __init__(self, header_reader: Optional[HeaderReader] = None, temp_writer: Optional[TempHeaderWriter] = None):
        self._reader = header_reader or PandasHeaderReader()
        self._temp_writer = temp_writer  # optional dependency for writing temp files

    # ---- DataFrame ----
    def obtener_columnas_df(self, req: DataFrameColumnsRequest) -> List[str]:
        """
        Validate the request and return the DataFrame's columns as strings.
        """
        req.validate()
        columnas = list(map(str, req.df.columns.tolist()))
        log.info("DataFrame columns: %s", columnas)
        return columnas

    # ---- File ----
    def obtener_columnas_archivo(self, req: FileColumnsRequest) -> FileColumnsResult:
        """
        Validate, read headers from file efficiently (nrows=0), and optionally
        generate a temp CSV containing only the header row.
        """
        req.validate()
        path = Path(req.path)

        columnas = self._reader.read_columns(path, sep=req.sep)
        log.info("Columns found in %s: %s", path, columnas)

        ruta_temp: Optional[str] = None
        if req.crear_temp:
            if self._temp_writer is None:
                # Lazily instantiate a default writer if none was injected
                self._temp_writer = LocalTempHeaderWriter()
            ruta_temp = self._temp_writer.write_header_temp(columnas)
            log.info("Temporary header file created: %s", ruta_temp)

        return FileColumnsResult(columnas=columnas, ruta_temp=ruta_temp)


# =============================================================================
# FACADES / COMPATIBILITY (procedural API)
# =============================================================================
def obtener_columnas_df(df: pd.DataFrame) -> List[str]:
    """
    Compatibility with your original function. Replaces prints with logging and validates inputs.
    """
    service = ColumnsService()
    return service.obtener_columnas_df(DataFrameColumnsRequest(df=df))


def obtener_columnas_archivo(
    ruta_archivo: str | Path,
    crear_temp: bool = False,        # by default DO NOT write to disk
    sep: Optional[str] = ",",        # if None, attempt delimiter inference
) -> Tuple[List[str], Optional[str]]:
    """
    Compatibility with your original function. Optimized header read (nrows=0).
    If crear_temp=True, writes a temporary CSV with only headers and returns its path.
    """
    service = ColumnsService()
    result = service.obtener_columnas_archivo(
        FileColumnsRequest(path=ruta_archivo, sep=sep, crear_temp=crear_temp)
    )
    return result.columnas, result.ruta_temp