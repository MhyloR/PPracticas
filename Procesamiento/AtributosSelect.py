import re
from pathlib import Path
from typing import Dict, Optional, Any
import pandas as pd
import tempfile

ALMACEN_DIR = Path("Almacenamiento")  # Se creará si no existe


# -----------------------------
# Utilidades
# -----------------------------
def _sanitize_filename(text: Any) -> str:
    """Convierte un valor arbitrario en un nombre de archivo seguro."""
    if pd.isna(text):
        return "valor_vacio"
    s = str(text).strip().replace(" ", "_")
    # Elimina caracteres inválidos para nombres de archivo (Windows/Unix)
    s = re.sub(r'[\\/:*?"<>|]+', "", s)
    # Colapsa múltiples '_'
    s = re.sub(r"_+", "_", s)
    # Limita longitud por compatibilidad con distintos FS
    s = s[:120] if len(s) > 120 else s
    return s or "valor_vacio"


def _siguiente_ruta_disponible(base: Path) -> Path:
    """
    Dada una ruta base, si existe, genera base__1, base__2, ... hasta que no exista.
    Ej: 'col_val.csv' -> 'col_val__1.csv', etc.
    """
    if not base.exists():
        return base
    stem, suffix = base.stem, base.suffix
    contador = 1
    while True:
        candidata = base.with_name(f"{stem}__{contador}{suffix}")
        if not candidata.exists():
            return candidata
        contador += 1


def _elegir_columna_interactivo(df: pd.DataFrame) -> str:
    """Muestra columnas y permite elegir por número o por nombre (exacto)."""
    columnas = list(df.columns)
    print("\nColumnas disponibles:")
    for i, c in enumerate(columnas, start=1):
        print(f"  {i}. {c}")

    entrada = input("\nElige la columna (número o nombre exacto): ").strip()
    if not entrada:
        raise ValueError("No ingresaste una selección de columna.")

    # Intento por número
    if entrada.isdigit():
        idx = int(entrada)
        if not (1 <= idx <= len(columnas)):
            raise IndexError(f"Índice fuera de rango (1..{len(columnas)}).")
        return columnas[idx - 1]

    # Intento por nombre exacto (respeta mayúsculas/acentos)
    if entrada in df.columns:
        return entrada

    # Intento tolerante: ignorando espacios extremos
    candidato = entrada.strip()
    if candidato in df.columns:
        return candidato

    raise KeyError(f"La columna '{entrada}' no existe. Revisa la lista mostrada.")


def _elegir_valor_interactivo(serie: pd.Series) -> Any:
    """
    Lista valores únicos (preservando orden de aparición), muestra conteos y permite elegir uno.
    Retorna el valor real seleccionado (incluye NaN si se elige).
    """
    serie_obj = serie.astype("object")

    # Preserva orden de aparición
    valores_unicos = serie_obj.drop_duplicates(keep="first")

    # Asegura incluir NaN explícitamente si existe (y no está ya)
    if serie_obj.isna().any() and not valores_unicos.isna().any():
        valores_unicos = pd.concat([valores_unicos, pd.Series([float("nan")])], ignore_index=True)

    # Arma lista [(label, valor_real, conteo)]
    items = []
    for v in valores_unicos:
        if pd.isna(v):
            cnt = serie_obj.isna().sum()
            label = "NaN"
        else:
            cnt = (serie_obj == v).sum()
            label = str(v)
        items.append((label, v, cnt))

    # Métricas informativas
    unicos_con_nombre = [it for it in items if not pd.isna(it[1])]
    filas_nan = serie_obj.isna().sum()

    print("\nResumen de la columna seleccionada:")
    print(f"  - Valores con nombre (no vacíos): {len(unicos_con_nombre)}")
    print(f"  - Filas NaN (vacías): {filas_nan}")

    print("\nValores disponibles (en orden de aparición):")
    for i, (label, _valor, cnt) in enumerate(items, start=1):
        print(f"  {i}. {label}  →  {cnt} filas")

    entrada = input("\nElige el valor (número o etiqueta exacta mostrada): ").strip()
    if not entrada:
        raise ValueError("No ingresaste una selección de valor.")

    # Por número
    if entrada.isdigit():
        idx = int(entrada)
        if not (1 <= idx <= len(items)):
            raise IndexError(f"Índice fuera de rango (1..{len(items)}).")
        return items[idx - 1][1]

    # Por etiqueta exacta (la que imprimimos)
    for label, valor, _cnt in items:
        if entrada == label:
            return valor

    raise KeyError(f"El valor '{entrada}' no se encuentra en la lista mostrada.")


# -----------------------------
# Núcleo de exportación
# -----------------------------
def exportar_por_columna(
    df: pd.DataFrame,
    columna: str,
    carpeta_salida: Path | str | None = None,
    prefijo_archivo: Optional[str] = None,
    guardar_indice: bool = False,
    crear_carpeta_si_no_existe: bool = True,
    valor_objetivo: Optional[Any] = None,
):
    """
    Exporta CSV según 'valor_objetivo'.

    Por defecto (cuando `carpeta_salida` es None) cada resultado se guarda en
    un **archivo temporal** y el diccionario devuelto usa las rutas de dichos
    archivos. Si se proporciona `carpeta_salida` se seguirá el comportamiento
    clásico de escribir en disco dentro de esa carpeta (creándola si es
    necesario).

    Retorna:
        resultados -> dict con {ruta_archivo: filas}
        subset     -> df filtrado según el valor elegido
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("El parámetro 'df' debe ser un pandas.DataFrame.")
    if columna not in df.columns:
        raise KeyError(f"La columna '{columna}' no existe. Columnas disponibles: {list(df.columns)}")

    usar_temp = carpeta_salida is None
    carpeta: Path | None = None
    if not usar_temp:
        # inicializar carpeta únicamente si no se usarán archivos temporales
        carpeta = Path(carpeta_salida)  # type: ignore[arg-type]
        if not carpeta.exists():
            if crear_carpeta_si_no_existe:
                carpeta.mkdir(parents=True, exist_ok=True)
            else:
                raise FileNotFoundError(f"La carpeta destino '{carpeta}' no existe.")

    # cuando usar_temp es True no se emplea la variable `carpeta` en absoluto

    serie = df[columna].astype("object")

    resultados = {}
    safe_prefix = _sanitize_filename((prefijo_archivo or columna).strip())

    # --- Exportar SOLO el valor elegido ---
    if valor_objetivo is not None:

        if pd.isna(valor_objetivo):
            mascara = serie.isna()
            etiqueta = "NaN"
        else:
            mascara = serie == valor_objetivo
            etiqueta = str(valor_objetivo)

        subset = df.loc[mascara]

        if subset.empty:
            return {}, subset

        safe_val = _sanitize_filename(etiqueta)
        if usar_temp:
            tmp = tempfile.NamedTemporaryFile(prefix=f"{safe_prefix}_{safe_val}_", suffix=".csv", delete=False)
            ruta_final = tmp.name
            tmp.close()
        else:
            assert carpeta is not None  # carpeta sólo puede ser None si usar_temp es True
            ruta = carpeta / f"{safe_prefix}_{safe_val}.csv"
            ruta_final = _siguiente_ruta_disponible(ruta)

        subset.to_csv(ruta_final, index=guardar_indice)
        resultados[str(ruta_final)] = len(subset)

        return resultados, subset  # ← DEVUELVE EL DATAFRAME FILTRADO

    # --- Exportar TODOS (modo clásico) ---
    valores_unicos = serie.drop_duplicates(keep="first")

    if serie.isna().any() and not valores_unicos.isna().any():
        valores_unicos = pd.concat([valores_unicos, pd.Series([float('nan')])], ignore_index=True)

    # Exportación en lote
    for val in valores_unicos:
        if pd.isna(val):
            mascara = serie.isna()
            etiqueta = "NaN"
        else:
            mascara = serie == val
            etiqueta = str(val)

        subset = df.loc[mascara]

        if subset.empty:
            continue

        safe_val = _sanitize_filename(etiqueta)
        if usar_temp:
            tmp = tempfile.NamedTemporaryFile(prefix=f"{safe_prefix}_{safe_val}_", suffix=".csv", delete=False)
            ruta_final = tmp.name
            tmp.close()
        else:
            assert carpeta is not None
            ruta = carpeta / f"{safe_prefix}_{safe_val}.csv"
            ruta_final = _siguiente_ruta_disponible(ruta)

        subset.to_csv(ruta_final, index=guardar_indice)
        resultados[str(ruta_final)] = len(subset)

    return resultados, df  # ← si exporta todo, devuelve df original

def ejecutar_interactivo(df: pd.DataFrame):
    print("=== Exportar CSV por un valor específico de una columna ===")
    print("Generando archivos temporales (no se usa carpeta fija)")

    columna = _elegir_columna_interactivo(df)
    print(f"\nTrabajando con la columna: {columna}")

    valor = _elegir_valor_interactivo(df[columna])

    resultados, df_seleccion = exportar_por_columna(
        df=df,
        columna=columna,
        carpeta_salida=None,
        prefijo_archivo=columna,
        guardar_indice=False,
        crear_carpeta_si_no_existe=True,
        valor_objetivo=valor
    )

    if not resultados:
        print("\n[INFO] No se generó archivo (subset vacío).")
        return df_seleccion

    total = sum(resultados.values())
    print(f"\n[OK] Se generó {len(resultados)} archivo(s).")
    print(f"[OK] Filas exportadas: {total}")

    for ruta, n in sorted(resultados.items()):
        print(f"  - {Path(ruta).name} → {n} filas")

    return df_seleccion  # ← AQUÍ DEVUELVE EL DF FILTRADO