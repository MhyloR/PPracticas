import pandas as pd
from Lectura.Api import get_df_unificado
from Lectura.APlano import load_to_dataframe
from Procesamiento.Divide import Separacion
from Procesamiento.AtribSelect import ejecutar_interactivo
from Procesamiento.GetColumns import obtener_columnas_df
from Procesamiento.plot_dataframe import plot_series_desde_lista
from datetime import date
from dateutil.relativedelta import relativedelta   # viene con python‑dateutil

hoy = date.today()
tres_meses_atras = hoy - relativedelta(months=32)

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

data = []
### FIltro de columnas


def si_no(prompt: str) -> bool:
    while True:
        r = input(f"{prompt} (s/n): ").strip().lower()
        if r in ("s", "n"):
            return r == "s"
        print("→ Por favor responde con 's' o 'n'.")

y = True
while y:
    print("\n=== Nueva ronda de filtrado ===")
    df_filtro = ejecutar_interactivo(df)

    while si_no("¿Añadir otro filtro sobre el resultado actual?"):
        df_filtro = ejecutar_interactivo(df_filtro)

    data.append(df_filtro.copy())
    print("Resultado guardado.")

    y = si_no("¿Empezar a filtrar otro atributo (reiniciar desde df)?")

print(columnas)
sep =[]
for i in range(len(data)):
    df_filtro = data[i]
    df_general , meta = Separacion(columnas, df_filtro)
    sep.append(df_general)

#factor_de_escalado = input("Ingrese el factor de escalado para la segunda columna: ")
for i in range(len(sep)):
    df_general = sep[i]
    # Cambia la parte donde se asignan las columnas en df_general
    df_general.iloc[:, 0] = pd.to_datetime(df_general.iloc[:, 0])  # Convertir la primera columna a fecha
    df_general = df_general.sort_values(by=df_general.columns[0])  # Ordenar por la primera columna
    df_general.iloc[:, 1] = df_general.iloc[:, 1]  # Dividir la segunda columna por el factor de escalado

grafica = plot_series_desde_lista(sep,apilado=True)
print(grafica)