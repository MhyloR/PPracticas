# Api.py
from __future__ import annotations

# =============================================================================
# IMPORTS
# =============================================================================
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

import pandas as pd
import requests

try:
    # Librería SIMEM (asegúrate de tenerla instalada y accesible en tu entorno)
    from pydataxm.pydatasimem import ReadSIMEM
except Exception as e:  # ImportError u otros
    raise ImportError(
        "No se pudo importar 'pydataxm.pydatasimem'. "
        "Verifica que la librería esté instalada y accesible en tu entorno."
    ) from e


# =============================================================================
# LOGGING (puedes integrar con tu config global si ya tienes una)
# =============================================================================
def setup_logging(level: int | str = logging.INFO) -> None:
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        )


log = logging.getLogger(__name__)


# =============================================================================
# ERRORES (dominio / aplicación)
# =============================================================================
class AppError(Exception):
    """Error base de la aplicación."""


class ValidationError(AppError):
    """Error por entradas inválidas."""


class ExternalServiceError(AppError):
    """Error al consumir servicios externos (HTTP/SDK/etc.)."""


# =============================================================================
# DTOs / MODELOS DE DOMINIO
# =============================================================================
@dataclass(frozen=True)
class DatasetRequest:
    """
    Request de consulta a SIMEM.
    - dataset_id: identificador del dataset
    - fecha_inicio / fecha_final: en formato YYYY-MM-DD
    - include_namecolumns: si True, intenta obtener columnas "oficiales" vía ColumnsProvider;
      si False o si el proveedor no está, se usa df.columns
    """
    dataset_id: str
    fecha_inicio: str  # YYYY-MM-DD
    fecha_final: str   # YYYY-MM-DD
    include_namecolumns: bool = True

    def validate(self) -> None:
        if not isinstance(self.dataset_id, str) or not self.dataset_id.strip():
            raise ValidationError("dataset_id no puede ser vacío")
        for name, value in (("fecha_inicio", self.fecha_inicio), ("fecha_final", self.fecha_final)):
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except Exception as e:
                raise ValidationError(f"{name} debe estar en formato YYYY-MM-DD") from e
        if self.fecha_inicio > self.fecha_final:
            raise ValidationError("fecha_inicio no puede ser mayor que fecha_final")


@dataclass(frozen=True)
class DatasetResult:
    """Resultado con DataFrame y lista de columnas."""
    dataframe: pd.DataFrame
    namecolumns: List[str]


# =============================================================================
# PUERTOS / INTERFACES (DIP)
# =============================================================================
class SimemReader(ABC):
    @abstractmethod
    def fetch(self, req: DatasetRequest) -> pd.DataFrame:
        """Obtiene el DataFrame de SIMEM para el request dado."""
        raise NotImplementedError


class ColumnsProvider(ABC):
    @abstractmethod
    def get_namecolumns(self, dataset_id: str) -> List[str]:
        """Obtiene la lista de 'nameColumn' desde algún origen (HTTP, metadatos, etc.)."""
        raise NotImplementedError


# =============================================================================
# INFRA: ADAPTADOR SIMEM (ReadSIMEM)
# =============================================================================
class SimemReaderSIMEM(SimemReader):
    """
    Adaptador concreto que usa la librería ReadSIMEM.
    Devuelve DataFrame vacío si el SDK retorna None o un tipo inesperado.
    """
    def fetch(self, req: DatasetRequest) -> pd.DataFrame:
        try:
            simem = ReadSIMEM(req.dataset_id, req.fecha_inicio, req.fecha_final)
            df = simem.main()
        except Exception as e:
            log.error("Error al invocar ReadSIMEM: %r", e)
            raise ExternalServiceError(
                f"Fallo al consultar SIMEM para dataset={req.dataset_id}"
            ) from e

        if not isinstance(df, pd.DataFrame):
            log.warning("ReadSIMEM.main() devolvió %r; se usará DataFrame vacío", type(df))
            return pd.DataFrame()
        return df


# =============================================================================
# INFRA: ADAPTADOR HTTP PARA COLUMNAS
# =============================================================================
class HttpColumnsProvider(ColumnsProvider):
    """
    Proveedor de nameColumns vía HTTP usando una URL plantilla.
    - Reintentos con backoff ante errores transitorios (timeout, conexión, 5xx)
    - Extracción robusta de 'nameColumn' en estructuras JSON anidadas
    """
    def __init__(
        self,
        url_template: str,
        timeout: float = 20.0,
        retries: int = 3,
        backoff_base_seconds: float = 1.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        if "{dataset_id}" not in url_template:
            raise ValueError("url_template debe contener {dataset_id}")
        self.url_template = url_template
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff_base_seconds
        self.session = session or requests.Session()

    def get_namecolumns(self, dataset_id: str) -> List[str]:
        url = self.url_template.format(dataset_id=dataset_id)

        last_exc: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if 500 <= resp.status_code < 600:
                    raise requests.HTTPError(f"HTTP {resp.status_code} en {url}", response=resp)
                resp.raise_for_status()
                try:
                    data = resp.json()
                except ValueError as e:
                    raise ExternalServiceError(f"Respuesta no es JSON válido: {e}") from e
                if data is None:
                    raise ExternalServiceError("La respuesta JSON está vacía (None).")
                return self._extract_namecolumns_from_json(data)
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                last_exc = e
                if attempt < self.retries - 1:
                    delay = self.backoff * (2 ** attempt)
                    log.warning(
                        "Fallo al obtener nameColumns (intento %s/%s). Reintentando en %.1fs. Error: %r",
                        attempt + 1, self.retries, delay, e
                    )
                    time.sleep(delay)
                    continue
                break

        assert last_exc is not None
        raise ExternalServiceError(
            f"No fue posible obtener nameColumns: {last_exc!r}"
        ) from last_exc

    @staticmethod
    def _extract_namecolumns_from_json(obj: Union[Dict, List]) -> List[str]:
        found: List[str] = []

        def _collect(lst: List[Any], sink: List[str]) -> None:
            for item in lst:
                if isinstance(item, dict) and "nameColumn" in item:
                    val = item["nameColumn"]
                    if isinstance(val, str):
                        sink.append(val)

        def _walk(node: Union[Dict, List]) -> None:
            if isinstance(node, dict):
                for k, v in node.items():
                    if isinstance(k, str) and k.lower() == "columns":
                        if isinstance(v, list):
                            _collect(v, found)
                        elif isinstance(v, dict):
                            for key in ("items", "data", "list", "values"):
                                maybe = v.get(key)
                                if isinstance(maybe, list):
                                    _collect(maybe, found)
                    if isinstance(v, (dict, list)):
                        _walk(v)
            elif isinstance(node, list):
                for item in node:
                    if isinstance(item, (dict, list)):
                        _walk(item)

        _walk(obj)

        unique: List[str] = []
        seen = set()
        for col in found:
            if col not in seen:
                seen.add(col)
                unique.append(col)
        return unique


# =============================================================================
# SERVICIO (CASO DE USO)
# =============================================================================
class DatasetService:
    """
    Caso de uso: obtener DataFrame de SIMEM y columnas asociadas.
    - Si no se inyecta proveedor de columnas, usa df.columns.
    - Si el proveedor falla, hace fallback a df.columns y registra advertencia.
    """
    def __init__(self, reader: SimemReader, columns_provider: Optional[ColumnsProvider] = None):
        self._reader = reader
        self._columns_provider = columns_provider

    def obtener(self, req: DatasetRequest) -> DatasetResult:
        req.validate()

        df = self._reader.fetch(req)
        if not isinstance(df, pd.DataFrame):
            log.warning("El lector devolvió un tipo inesperado %r; se usará DataFrame vacío", type(df))
            df = pd.DataFrame()

        if req.include_namecolumns and self._columns_provider is not None:
            try:
                namecolumns = self._columns_provider.get_namecolumns(req.dataset_id)
            except Exception as e:
                log.warning("No fue posible obtener nameColumns desde proveedor: %r. Fallback a df.columns", e)
                namecolumns = list(map(str, df.columns))
        else:
            namecolumns = list(map(str, df.columns))

        return DatasetResult(dataframe=df, namecolumns=namecolumns)


# =============================================================================
# FACADES / COMPATIBILIDAD (funciones estilo procedural)
# =============================================================================
def obtener_namecolumns(
    dataset_id: str,
    url_template: str,
    timeout: float = 20.0,
    retries: int = 3,
    backoff_base_seconds: float = 1.0,
) -> List[str]:
    """
    Facade para obtener nameColumns desde HTTP en una sola llamada.
    Mantiene un API procedural sencillo.
    """
    provider = HttpColumnsProvider(
        url_template=url_template,
        timeout=timeout,
        retries=retries,
        backoff_base_seconds=1.0 if backoff_base_seconds is None else backoff_base_seconds,
    )
    return provider.get_namecolumns(dataset_id)


def get_df_unificado(
    dataset_id: str,
    fecha_inicio: str,
    fecha_final: str,
    url_template_namecols: Optional[str] = None,
    include_namecolumns: bool = False,
    timeout_namecols: float = 20.0,
    retries_namecols: int = 3,
) -> Dict[str, Any]:
    """
    Obtiene el DataFrame desde SIMEM y las columnas asociadas.
    - No escribe CSV a disco.
    - Si include_namecolumns=True y se pasa url_template_namecols, consulta el endpoint.
      Si falla o no se provee URL, usa df.columns como fallback.
    Retorna:
      {"dataframe": pd.DataFrame, "namecolumns": list[str]}
    """
    req = DatasetRequest(
        dataset_id=dataset_id,
        fecha_inicio=fecha_inicio,
        fecha_final=fecha_final,
        include_namecolumns=include_namecolumns,
    )
    reader = SimemReaderSIMEM()

    columns_provider: Optional[ColumnsProvider] = None
    if include_namecolumns and url_template_namecols:
        columns_provider = HttpColumnsProvider(
            url_template=url_template_namecols,
            timeout=timeout_namecols,
            retries=retries_namecols,
            backoff_base_seconds=1.0,
        )

    service = DatasetService(reader=reader, columns_provider=columns_provider)
    result = service.obtener(req)
    return {"dataframe": result.dataframe, "namecolumns": result.namecolumns}