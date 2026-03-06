# ejemplo_minimo.py
from click import Path
import pandas as pd
from Lectura.Api import get_df_unificado
from Lectura.Aplano import load_to_dataframe
from Procesamiento.AtributosSelect import ejecutar_interactivo
from Procesamiento.Separacion import Separacion
from datetime import date
from dateutil.relativedelta import relativedelta
from Procesamiento.ObtenerColumnas import obtener_columnas_df   # viene con python‑dateutil
from Procesamiento.temp_write import guardar_csv_temporal_en_almacenamiento

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



ruta = guardar_csv_temporal_en_almacenamiento(df)

print("CSV temporal generado en:", ruta)
print("Contenido del archivo:")
print(Path(ruta).read_text(encoding="utf-8"))

# Ejemplo: verificar existencia
print("¿Existe?", Path(ruta).exists())

print("Filas:", len(df))
print("Columnas:", namecolumns)


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


print(namecolumns)

sep =[]
for i in range(len(data)):
    df_filtro = data[i]
    df_general , meta = Separacion(namecolumns, df_filtro)
    sep.append(df_general)

factor_de_escalado = float(input("Ingrese el factor de escalado para la segunda columna: "))

for i in range(len(sep)):
    df_general = sep[i].copy()
    df_general.iloc[:, 0] = pd.to_datetime(df_general.iloc[:, 0], errors="coerce")
    df_general = df_general.dropna(subset=[df_general.columns[0]])
    df_general = df_general.sort_values(by=df_general.columns[0])
    df_general.iloc[:, 1] = df_general.iloc[:, 1].div(float(factor_de_escalado))
    sep[i] = df_general



