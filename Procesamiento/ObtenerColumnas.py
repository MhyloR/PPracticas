# ApiColumnas.py
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
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )

log = logging.getLogger(__name__)


# =============================================================================
# ERRORES
# =============================================================================
class AppError(Exception):
    """Error base de la aplicación."""

class ValidationError(AppError):
    """Entradas inválidas o inconsistentes."""

class FileReadError(AppError):
    """Errores al leer el archivo."""

class TempWriteError(AppError):
    """Errores al crear o escribir archivos temporales."""


# =============================================================================
# DTOs
# =============================================================================
@dataclass(frozen=True)
class DataFrameColumnsRequest:
    df: pd.DataFrame

    def validate(self) -> None:
        if self.df is None or not isinstance(self.df, pd.DataFrame):
            raise ValidationError("El DataFrame no puede ser None y debe ser un pd.DataFrame")


@dataclass(frozen=True)
class FileColumnsRequest:
    """
    path: ruta al archivo plano (CSV/TSV/TXT)
    sep: separador esperado; si None, se intentará inferir (pandas sep=None con engine='python')
    crear_temp: si True, se creará un archivo temporal con solo cabeceras
    """
    path: Path | str
    sep: Optional[str] = ","
    crear_temp: bool = False

    def validate(self) -> None:
        p = Path(self.path)
        if not p.exists():
            raise ValidationError(f"No se encontró el archivo: {p}")
        # Validar separador común si se provee
        if self.sep is not None and not isinstance(self.sep, str):
            raise ValidationError("sep debe ser una cadena o None")


@dataclass(frozen=True)
class FileColumnsResult:
    columnas: List[str]
    ruta_temp: Optional[str] = None


# =============================================================================
# PUERTOS / INTERFACES
# =============================================================================
class HeaderReader:
    """Puerto para leer solo encabezados/columnas de un archivo tabular."""
    def read_columns(self, path: Path, sep: Optional[str]) -> List[str]:
        raise NotImplementedError


class TempHeaderWriter:
    """Puerto para escribir un archivo temporal con solo las cabeceras."""
    def write_header_temp(self, columnas: List[str]) -> str:
        raise NotImplementedError


# =============================================================================
# INFRASTRUCTURE (adaptadores concretos)
# =============================================================================
class PandasHeaderReader(HeaderReader):
    """
    Lee únicamente las cabeceras. Optimización: usa nrows=0 para no cargar datos.
    Si sep es None, se permite inferencia con sep=None y engine='python'.
    """
    def read_columns(self, path: Path, sep: Optional[str]) -> List[str]:
        try:
            if sep is None:
                df = pd.read_csv(path, sep=None, engine="python", nrows=0)
            else:
                df = pd.read_csv(path, sep=sep, nrows=0)
            return list(map(str, df.columns.tolist()))
        except FileNotFoundError as e:
            raise FileReadError(f"Archivo no encontrado: {path}") from e
        except Exception as e:
            raise FileReadError(f"Error al leer cabeceras de {path}: {e}") from e


class LocalTempHeaderWriter(TempHeaderWriter):
    """
    Crea un archivo temporal (.csv) con solo la fila de cabeceras.
    Se limita a cabeceras, sin datos.
    """
    def write_header_temp(self, columnas: List[str]) -> str:
        try:
            tmp = tempfile.NamedTemporaryFile(prefix="cols_", suffix=".csv", delete=False)
            # Escribir cabecera como una sola línea CSV
            # Nota: usamos pandas para respetar escapes/citas correctamente
            pd.DataFrame(columns=columnas).head(0).to_csv(tmp.name, index=False)
            tmp.close()
            return tmp.name
        except Exception as e:
            raise TempWriteError(f"No se pudo crear archivo temporal de cabeceras: {e}") from e


# =============================================================================
# SERVICIO (caso de uso)
# =============================================================================
class ColumnsService:
    """
    - obtener_columnas_df: retorna nombres de columnas de un DataFrame (valida y sin prints).
    - obtener_columnas_archivo: retorna columnas de un archivo usando HeaderReader y,
      opcionalmente, crea un CSV temporal con solo cabeceras a través de TempHeaderWriter.
    """
    def __init__(self, header_reader: Optional[HeaderReader] = None, temp_writer: Optional[TempHeaderWriter] = None):
        self._reader = header_reader or PandasHeaderReader()
        self._temp_writer = temp_writer  # opcional

    # ---- DataFrame ----
    def obtener_columnas_df(self, req: DataFrameColumnsRequest) -> List[str]:
        req.validate()
        columnas = list(map(str, req.df.columns.tolist()))
        log.info("Columnas del DataFrame: %s", columnas)
        return columnas

    # ---- Archivo ----
    def obtener_columnas_archivo(self, req: FileColumnsRequest) -> FileColumnsResult:
        req.validate()
        path = Path(req.path)

        columnas = self._reader.read_columns(path, sep=req.sep)
        log.info("Columnas encontradas en %s: %s", path, columnas)

        ruta_temp: Optional[str] = None
        if req.crear_temp:
            if self._temp_writer is None:
                # Crear writer por defecto si no fue inyectado
                self._temp_writer = LocalTempHeaderWriter()
            ruta_temp = self._temp_writer.write_header_temp(columnas)
            log.info("Archivo temporal de cabeceras creado: %s", ruta_temp)

        return FileColumnsResult(columnas=columnas, ruta_temp=ruta_temp)


# =============================================================================
# FACADES / COMPATIBILIDAD (API procedural)
# =============================================================================
def obtener_columnas_df(df: pd.DataFrame) -> List[str]:
    """
    Compatibilidad con tu función original. Reemplaza prints por logging y valida entradas.
    """
    service = ColumnsService()
    return service.obtener_columnas_df(DataFrameColumnsRequest(df=df))


def obtener_columnas_archivo(
    ruta_archivo: str | Path,
    crear_temp: bool = False,        # por defecto NO escribe a disco
    sep: Optional[str] = ",",        # si None, se intenta inferir
) -> Tuple[List[str], Optional[str]]:
    """
    Compatibilidad con tu función original. Lectura optimizada de cabeceras (nrows=0).
    Si crear_temp=True, escribe un archivo temporal con solo cabeceras y retorna su ruta.
    """
    service = ColumnsService()
    result = service.obtener_columnas_archivo(
        FileColumnsRequest(path=ruta_archivo, sep=sep, crear_temp=crear_temp)
    )
    return result.columnas, result.ruta_temp
