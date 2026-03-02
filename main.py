import pandas as pd
from Lectura.Api import get_df_unificado
from Lectura.APlano import load_to_dataframe
from Procesamiento.Separacion import Separacion
from Procesamiento.AtributosSelect import ejecutar_interactivo
from Procesamiento.ObtenerColumnas import obtener_columnas_df
from Procesamiento.plot_dataframe import cargar_datos, plot_todos
from datetime import date
from dateutil.relativedelta import relativedelta   # viene con python‑dateutil

hoy = date.today()
tres_meses_atras = hoy - relativedelta(months=1)

Seleccion = input('¿Trabajara con DataSets o con Archivos Planos? (D/A): ').lower()

if Seleccion == "d":
    print("cebolla")
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
        url_template_namecols="https://www.simem.co/backend-files/api/detalle-datos-publicos?datasetId={dataset_id}",
        nombre_csv=f"data_{input_set}.csv"
    )

    df = resultado["dataframe"]
    columnas = resultado["namecolumns"]

if Seleccion == "a":
    print("Tomate")
    ruta_archivo = input("Ingrese la ruta del archivo plano: ")
    df = load_to_dataframe(ruta_archivo)
    columnas = obtener_columnas_df(df)



### FIltro de columnas
df_filtro = ejecutar_interactivo(df)
print("¿Desea realizar otro filtro? (s/n)")
if input().lower() == "s":
    x = True
    while x == True:
        df_filtro = ejecutar_interactivo(df_filtro)
        print("¿Desea realizar otro filtro? (s/n)")
        respuesta = input().lower()
        if respuesta == "n":
            x = False


print(columnas)
df_general , meta = Separacion(columnas, df_filtro)

factor_de_escalado = input("Ingrese el factor de escalado para la segunda columna: ")
# Cambia la parte donde se asignan las columnas en df_general
df_general.iloc[:, 0] = pd.to_datetime(df_general.iloc[:, 0])  # Convertir la primera columna a fecha
df_general = df_general.sort_values(by=df_general.columns[0])  # Ordenar por la primera columna
df_general.iloc[:, 1] = df_general.iloc[:, 1].div(float(factor_de_escalado))  # Dividir la segunda columna por el factor de escalado

plot_todos(cargar_datos(df=df_general))