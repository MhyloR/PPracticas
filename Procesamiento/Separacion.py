import pandas as pd

def Separacion(columnas, archivo):
    """
    Separa un DataFrame en dos: uno con var_x y var_y (df_general), y otro con el resto (df_atributos).
    Permite renombrar interactivamente SOLO las dos columnas de df_general.

    Args:
        columnas: Lista de nombres de columnas disponibles (no usada, se valida desde el DataFrame).
        archivo: DataFrame de entrada.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (df_general con 2 columnas, df_atributos con el resto)
    """
    # Validaciones iniciales
    if not isinstance(archivo, pd.DataFrame):
        raise TypeError(f"Se esperaba DataFrame, recibido: {type(archivo)}")
    if archivo.empty:
        raise ValueError("El DataFrame está vacío")

    # Columnas válidas desde el DataFrame real
    columnas_validas = list(archivo.columns)

    # --- Selección de variable X ---
    while True:
        var_x = input("Variable eje X: ").strip()
        if var_x in columnas_validas:
            break
        print(f"Columna no encontrada. Disponibles: {columnas_validas}")

    # --- Selección de variable Y ---
    while True:
        var_y = input("Variable eje Y: ").strip()
        if var_y == var_x:
            print("La variable Y no puede ser igual a X")
            continue
        if var_y in columnas_validas:
            break
        print(f"Columna no encontrada. Disponibles: {columnas_validas}")

    # --- Construcción de df_general y df_atributos ---
    df_general = archivo[[var_x, var_y]].copy()

    # Convertir X a datetime (intento estricto + flexible)
    try:
        df_general[var_x] = pd.to_datetime(df_general[var_x], format='%Y-%m-%d %H:%M:%S')
    except Exception:
        df_general[var_x] = pd.to_datetime(df_general[var_x], errors='coerce', dayfirst=False)

    df_atributos = archivo.drop([var_x, var_y], axis=1).copy()

    # --- Renombrado interactivo de SOLO X e Y ---
    print("\n=== Renombrar columnas de df_general (solo X e Y) ===")
    print(f"Nombre actual de X: {var_x}")
    nuevo_x = input("Nuevo nombre para X (Enter para conservar): ").strip()
    if not nuevo_x:
        nuevo_x = var_x

    print(f"Nombre actual de Y: {var_y}")
    nuevo_y = input("Nuevo nombre para Y (Enter para conservar): ").strip()
    if not nuevo_y:
        nuevo_y = var_y

    # Validaciones de los nuevos nombres
    if not nuevo_x:
        raise ValueError("El nombre para X no puede ser vacío.")
    if not nuevo_y:
        raise ValueError("El nombre para Y no puede ser vacío.")
    if nuevo_x == nuevo_y:
        raise ValueError("Los nombres de X e Y no pueden ser iguales.")

    # Aplicar renombre en df_general
    df_general.rename(columns={var_x: nuevo_x, var_y: nuevo_y}, inplace=True)

    # Validaciones finales
    assert isinstance(df_general, pd.DataFrame), "df_general no es DataFrame"
    assert isinstance(df_atributos, pd.DataFrame), "df_atributos no es DataFrame"
    assert df_general.shape[1] == 2, f"df_general debe tener 2 columnas, tiene {df_general.shape[1]}"

    return df_general, df_atributos