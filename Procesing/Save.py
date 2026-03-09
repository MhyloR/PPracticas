import os
import pandas as pd
from typing import Tuple, Optional

class DataFrameExporter:
    """
    A utility class to export a pandas DataFrame to CSV and JSON files.

    Usage:
        exporter = DataFrameExporter(base_path="outputs", file_name="people")
        csv_path, json_path = exporter.export(df)

    You can also call methods individually:
        exporter.save_csv(df)
        exporter.save_json(df)
    """

    def __init__(self, base_path: str, file_name: str):
        """
        Initialize the exporter with a base folder and a base file name.

        Args:
            base_path (str): Target directory where files will be saved.
            file_name (str): File name without extension (e.g., "report_2026Q1").
        """
        self.base_path = base_path
        self.file_name = file_name

        # Ensure the target directory exists
        os.makedirs(self.base_path, exist_ok=True)

    @property
    def csv_path(self) -> str:
        """Full path for the CSV output."""
        return os.path.join(self.base_path, f"{self.file_name}.csv")

    @property
    def json_path(self) -> str:
        """Full path for the JSON output."""
        return os.path.join(self.base_path, f"{self.file_name}.json")

    def _validate_df(self, df: pd.DataFrame) -> None:
        """Internal helper to validate that the input is a non-empty DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected a pandas DataFrame.")
        if df.empty:
            # You can relax this if empty files are acceptable
            raise ValueError("The DataFrame is empty; nothing to export.")

    def save_csv(self, df: pd.DataFrame, index: bool = False, **to_csv_kwargs) -> str:
        """
        Save the DataFrame to CSV.

        Args:
            df (pd.DataFrame): Data to export.
            index (bool): Whether to include the index in the CSV. Defaults to False.
            **to_csv_kwargs: Additional keyword arguments passed to DataFrame.to_csv().

        Returns:
            str: The path of the saved CSV file.
        """
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
        """
        Save the DataFrame to JSON.

        Args:
            df (pd.DataFrame): Data to export.
            orient (str): JSON orientation; "records" is a list of objects (recommended).
            indent (Optional[int]): Indentation level for human-readable JSON. Use None for compact.
            force_ascii (bool): If False, keeps non-ASCII characters intact (recommended).
            **to_json_kwargs: Additional kwargs passed to DataFrame.to_json().

        Returns:
            str: The path of the saved JSON file.
        """
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
        Export the DataFrame to both CSV and JSON in one call.

        Args:
            df (pd.DataFrame): Data to export.
            csv_index (bool): Include index in CSV.
            json_orient (str): Orientation for JSON (e.g., "records", "split", "columns").
            json_indent (Optional[int]): Indentation for JSON; None for compact.
            json_force_ascii (bool): If True, escape non-ASCII characters.
            to_csv_kwargs (Optional[dict]): Extra options for DataFrame.to_csv().
            to_json_kwargs (Optional[dict]): Extra options for DataFrame.to_json().

        Returns:
            Tuple[str, str]: (csv_path, json_path)
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