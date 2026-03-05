# ejemplo_minimo.py
from Lectura.Api import get_df_unificado
from Lectura.Aplano import load_to_dataframe
from datetime import date
from dateutil.relativedelta import relativedelta
from Normal.Procesamiento.ObtenerColumnas import obtener_columnas_df   # viene con python‑dateutil

hoy = date.today()
tres_meses_atras = hoy - relativedelta(months=3)

Seleccion = input('¿Trabajara con DataSets o con Archivos Planos? (D/A): ').lower()

if Seleccion == "d":
    ## Solicitud de set##
    input_set = input("Ingrese el dataset ID a tratar: ")
    print("Porfavor, ingrese el rango de fechas a tratar, si no se ingresa nada, se tomara el ultimos tres meses de datos disponibles")
    FechaInicio = input("Ingrese la fecha de inicio (YYYY-MM-DD): ")

    if not FechaInicio:
        FechaInicio = tres_meses_atras.isoformat()

    print ("Fecha de inicio:", FechaInicio)
    FechaFin = input("Ingrese la fecha de fin (YYYY-MM-DD): ")
    if not FechaFin:
        FechaFin = hoy.isoformat()

    print ("Fecha de fin:", FechaFin)

    resultado = get_df_unificado(
        dataset_id=input_set,
        fecha_inicio=FechaInicio,
        fecha_final=FechaFin,
        include_namecolumns=False  # usa df.columns (no consulta endpoint)
    )

    df = resultado["dataframe"]
    namecolumns = resultado["namecolumns"]
    
if Seleccion == "a":
    print("Tomate")
    ruta_archivo = input("Ingrese la ruta del archivo plano: ")
    df = load_to_dataframe(ruta_archivo)
    namecolumns = obtener_columnas_df(df)
    
print("Filas:", len(df))
print("Columnas (df.columns):", namecolumns)