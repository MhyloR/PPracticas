# core/exporter.py
import os
import pandas as pd
from typing import Tuple, Optional

class DataFrameExporter:
    """
    Exporta un DataFrame a CSV y JSON en una carpeta destino (p. ej., 'Storage').
    Uso:
        exporter = DataFrameExporter(base_path="Storage", file_name="filtered_data_abc_2026-03-01_to_2026-03-18")
        csv_path, json_path = exporter.export(df)
    También puedes llamar save_csv / save_json por separado.
    """

    def __init__(self, base_path: str, file_name: str):
        """
        Args:
            base_path (str): Carpeta donde se guardarán los archivos (crea si no existe).
            file_name (str): Nombre base SIN extensión (p. ej., "filtered_data_xxx_2026-03-01_to_2026-03-18").
        """
        self.base_path = base_path
        self.file_name = file_name
        os.makedirs(self.base_path, exist_ok=True)

    @property
    def csv_path(self) -> str:
        return os.path.join(self.base_path, f"{self.file_name}.csv")

    @property
    def json_path(self) -> str:
        return os.path.join(self.base_path, f"{self.file_name}.json")

    def _validate_df(self, df: pd.DataFrame) -> None:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame.")
        if df.empty:
            # Si quieres permitir vacíos, elimina esta excepción
            raise ValueError("The DataFrame is empty; nothing to export.")

    def save_csv(self, df: pd.DataFrame, index: bool = False, **to_csv_kwargs) -> str:
        """Guarda en CSV y devuelve la ruta final."""
        self._validate_df(df)
        df.to_csv(self.csv_path, index=index, **to_csv_kwargs)
        return self.csv_path

    def save_json(
        self,
        df: pd.DataFrame,
        orient: str = "records",
        indent: Optional[int] = 4,
        force_ascii: bool = False,
        **to_json_kwargs
    ) -> str:
        """Guarda en JSON (por defecto como lista de objetos) y devuelve la ruta final."""
        self._validate_df(df)
        df.to_json(
            self.json_path,
            orient=orient,
            indent=indent,
            force_ascii=force_ascii,
            **to_json_kwargs
        )
        return self.json_path

    def export(
        self,
        df: pd.DataFrame,
        csv_index: bool = False,
        json_orient: str = "records",
        json_indent: Optional[int] = 4,
        json_force_ascii: bool = False,
        to_csv_kwargs: Optional[dict] = None,
        to_json_kwargs: Optional[dict] = None,
    ) -> Tuple[str, str]:
        """
        Exporta a CSV + JSON en una sola llamada.
        Devuelve (csv_path, json_path).
        """
        to_csv_kwargs = to_csv_kwargs or {}
        to_json_kwargs = to_json_kwargs or {}

        csv_path = self.save_csv(df, index=csv_index, **to_csv_kwargs)
        json_path = self.save_json(
            df,
            orient=json_orient,
            indent=json_indent,
            force_ascii=json_force_ascii,
            **to_json_kwargs
        )
        return csv_path, json_path


def build_export_base_name(dataset_id: str, fecha_inicio: str, fecha_final: str) -> str:
    """
    Construye el nombre base estándar:
      'filtered_data_{dataset_id}_{fecha_inicio}_to_{fecha_final}'
    (Asume fechas en formato 'YYYY-MM-DD')
    """
    return f"filtered_data_{dataset_id}_{fecha_inicio}_to_{fecha_final}"