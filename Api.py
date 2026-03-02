import sys
import os
from pydataxm.pydatasimem import ReadSIMEM, CatalogSIMEM
import pandas as pd
import requests
import tempfile
from typing import List, Any, Dict, Union

# ---------------------------------------------------------
# 1. FUNCIÓN REUTILIZABLE PARA OBTENER nameColumns
# ---------------------------------------------------------
def obtener_namecolumns(dataset_id: str, url_template: str, timeout: int = 200) -> List[str]:

    if "{dataset_id}" not in url_template:
        raise ValueError("El url_template debe contener {dataset_id}")

    url = url_template.format(dataset_id=dataset_id)
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError as e:
        raise ValueError(f"La respuesta no es JSON válido: {e}")

    if data is None:
        raise ValueError("La respuesta JSON está vacía (None).")

    # --- Recorrido recursivo ---
    def _find_namecolumns(obj: Union[Dict, List]) -> List[str]:
        found = []

        def _walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    if k.lower() == "columns":  
                        if isinstance(v, list):
                            for item in v:
                                if isinstance(item, dict) and "nameColumn" in item:
                                    found.append(item["nameColumn"])
                        elif isinstance(v, dict):
                            for possible in ("items", "data", "list", "values"):
                                if possible in v and isinstance(v[possible], list):
                                    for item in v[possible]:
                                        if isinstance(item, dict) and "nameColumn" in item:
                                            found.append(item["nameColumn"])
                    _walk(v)
            elif isinstance(node, list):
                for n in node:
                    _walk(n)

        _walk(obj)

        # Únicos manteniendo el orden
        seen = set()
        unique = []
        for col in found:
            if col not in seen:
                seen.add(col)
                unique.append(col)
        return unique

    return _find_namecolumns(data)


# ---------------------------------------------------------
# 2. FUNCIÓN PRINCIPAL UNIFICADA
# ---------------------------------------------------------
def get_df_unificado(
    dataset_id: str,
    fecha_inicio: str,
    fecha_final: str,
    url_template_namecols: str,
    nombre_csv: str | None = None,
) -> Dict[str, Any]:
    """
    Descarga el dataset desde SIMEM, obtiene nameColumns vía API y guarda el CSV
    en un archivo temporal. El archivo temporal se crea con la librería
    estándar `tempfile` y se devuelve su ruta en el diccionario resultante.
    Si se especifica `nombre_csv`, se usará ese nombre dentro del directorio
    de almacenamiento (antigua conducta), pero por defecto se crean archivos
    temporales para no dejar residuos.

    La escritura del CSV se realiza **antes** de consultar el endpoint de
    columnas; cualquier fallo en esa llamada se captura y no evita el retorno
    del diccionario, de modo que siempre se puede inspeccionar `ruta_csv`.
    """

    # --- Obtener dataframe desde SIMEM ---
    catalogo = CatalogSIMEM(catalog_type='Datasets')
    df_catalogo = catalogo.get_data()

    simem = ReadSIMEM(dataset_id, fecha_inicio, fecha_final)
    df_general = simem.main()

    if df_general is None:
        print("Advertencia: ReadSIMEM.main() devolvió None. Se genera DataFrame vacío.")
        df_general = pd.DataFrame()

    # --- Determinar ruta de salida ---
    if nombre_csv:
        # comportamiento legado: escribir en carpeta Almacenamiento
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.getcwd()
        carpeta_dos_arriba = os.path.abspath(os.path.join(base_dir, "..", ".."))
        if not os.path.isdir(carpeta_dos_arriba):
            raise FileNotFoundError(
                f"No existe la carpeta dos niveles arriba: {carpeta_dos_arriba}"
            )
        carpeta_almacenamiento = os.path.join(carpeta_dos_arriba, "Almacenamiento")
        os.makedirs(carpeta_almacenamiento, exist_ok=True)
        ruta_csv = os.path.join(carpeta_almacenamiento, nombre_csv)
    else:
        # crear archivo temporal en el sistema (se mantiene tras cerrar)
        # el nombre devuelto se utiliza para almacenamiento externo y puede
        # inspeccionarse/leer desde otra parte del código o el notebook.
        tmp = tempfile.NamedTemporaryFile(prefix="simem_", suffix=".csv", delete=False)
        ruta_csv = tmp.name
        tmp.close()

    # Guardar CSV
    df_general.to_csv(ruta_csv, index=False, encoding="utf-8")
    print(f"CSV guardado en: {ruta_csv}")

    # --- Obtener columnas del endpoint; fallo no debe abortar ---
    try:
        namecolumns = obtener_namecolumns(dataset_id, url_template_namecols)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Advertencia: error al obtener nameColumns: {exc}")
        namecolumns = []

    # --- Retornar ambos resultados ---
    return {
        "dataframe": df_general,
        "namecolumns": namecolumns,
        "ruta_csv": ruta_csv,
    }