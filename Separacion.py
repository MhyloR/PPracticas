import pandas as pd

def Separacion(columnas, archivo):
    """
    Separa un DataFrame en dos: uno con var_x y var_y, otro con el resto.
    
    Args:
        columnas: Lista de nombres de columnas disponibles
        archivo: DataFrame de entrada
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: (df_general con 2 cols, df_atributos con el resto)
    """
    # Validar que archivo es un DataFrame
    if not isinstance(archivo, pd.DataFrame):
        raise TypeError(f"Se esperaba DataFrame, recibido: {type(archivo)}")
    
    if archivo.empty:
        raise ValueError("El DataFrame está vacío")
    
    # Obtener columnas válidas del DataFrame real
    columnas_validas = list(archivo.columns)
    
    # Solicitar variable X
    while True:
        var_x = input("Variable eje X: ").strip()
        if var_x in columnas_validas:
            break
        print(f"Columna no encontrada. Disponibles: {columnas_validas}")

    # Solicitar variable Y
    while True:
        var_y = input("Variable eje y: ").strip()
        if var_y in columnas_validas:
            break
        if var_y == var_x:
            print("La variable Y no puede ser igual a X")
            continue
        print(f"Columna no encontrada. Disponibles: {columnas_validas}")

    # Seleccionar columnas y crear copia
    df_general = archivo[[var_x, var_y]].copy()
    
    # Validar que df_general es DataFrame
    if not isinstance(df_general, pd.DataFrame):
        raise TypeError("Error al crear df_general")
    
    # Intentar convertir X a datetime
    try:
        # Tu formato "ideal"
        df_general[var_x] = pd.to_datetime(df_general[var_x], format='%Y-%m-%d %H:%M:%S')
    except Exception:
        # Fallback flexible si hay variaciones
        df_general[var_x] = pd.to_datetime(df_general[var_x], errors='coerce', dayfirst=False)

    # Crear df con atributos restantes
    df_atributos = archivo.drop([var_x, var_y], axis=1)
    
    # Validar resultados
    assert isinstance(df_general, pd.DataFrame), "df_general no es DataFrame"
    assert isinstance(df_atributos, pd.DataFrame), "df_atributos no es DataFrame"
    assert df_general.shape[1] == 2, f"df_general debe tener 2 columnas, tiene {df_general.shape[1]}"

    return df_general, df_atributos
