import pandas as pd
import tempfile

def obtener_columnas_df(df: pd.DataFrame) -> list:
    """
    Retorna la lista de nombres de columnas de un DataFrame.

    Args:
        df (pd.DataFrame): DataFrame del que se quieren las columnas.

    Returns:
        list: nombres de las columnas.
    """
    if df is None:
        raise ValueError("El DataFrame no puede ser None")
    columnas = df.columns.tolist()
    print(f"Columnas del DataFrame: {columnas}")
    return columnas

# si aún se necesita leer desde un archivo plano
def obtener_columnas_archivo(ruta_archivo, crear_temp: bool = True):
    """
    Lee un archivo plano y retorna sus columnas.

    Si `crear_temp` es True se genera un archivo temporal con sólo las
    cabeceras (mismas columnas) y se devuelve la ruta junto con la lista de
    columnas; esto asegura que cualquier fichero que produzca este código sea
    temporal y no deje residuos.

    Args:
        ruta_archivo (str): camino al archivo CSV.
        crear_temp (bool): controla la creación del fichero temporal.

    Returns:
        tuple[list, Optional[str]]: (columnas, ruta_temp)
    """
    try:
        df = pd.read_csv(ruta_archivo, sep=',', nrows=1)  # ajustar sep si hace falta
        columnas = df.columns.tolist()
        print(f"Columnas encontradas: {columnas}")

        ruta_temp = None
        if crear_temp:
            tmp = tempfile.NamedTemporaryFile(prefix="cols_", suffix=".csv", delete=False)
            df.head(0).to_csv(tmp.name, index=False)
            ruta_temp = tmp.name
            tmp.close()
            print(f"Archivo temporal creado: {ruta_temp}")

        return columnas, ruta_temp
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo en {ruta_archivo}")
        return [], None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return [], None


