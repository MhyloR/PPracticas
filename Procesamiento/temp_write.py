import csv
import tempfile
from pathlib import Path
import os
import pandas as pd


def guardar_csv_temporal_en_almacenamiento(df: pd.DataFrame) -> str:
    """
    Guarda un DataFrame como CSV temporal dentro de la carpeta 'Almacenamiento'.
    Devuelve la ruta del archivo temporal.
    """

    # Crear carpeta Almacenamiento si no existe
    carpeta = Path("Almacenamiento")
    carpeta.mkdir(parents=True, exist_ok=True)

    # Crear archivo temporal dentro de la carpeta
    temp = tempfile.NamedTemporaryFile(
        mode="w+", 
        delete=False,            # No se borra automáticamente
        newline="",
        encoding="utf-8",
        dir=str(carpeta),
        prefix="temp_",
        suffix=".csv"
    )

    # Escribir CSV usando csv.writer
    writer = csv.writer(temp)

    # Escribir cabeceras
    writer.writerow(df.columns.tolist())

    # Escribir filas
    for row in df.itertuples(index=False, name=None):
        writer.writerow(row)

    temp.flush()
    temp.close()

    return temp.name