import duckdb
import pandas as pd

### Lectura de datos desde un CSV, si o que

#duckdb.read_csv("example.csv") # Lee el archivo CSV y devuelve la dataframe resultante
### Se pueden leer varios CSV a la vez
#duckdb.read_csv("Test/*.csv") # Lee todos los archivos CSV en la carpeta "folder" y devuelve una dataframe combinada

#duckdb.sql("SELECT * FROM 'Test/example.csv'").show() # Ejecuta una consulta SQL directamente sobre el archivo CSV y devuelve el resultado como dataframe

## El formato sirve tambien para archivos JSON, Parquet, etc. Solo hay que cambiar la extensión del archivo en la consulta SQL

test_df = pd.DataFrame.from_dict({"i": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]})
#print(duckdb.sql("SELECT * FROM test_df").fetchall())

## Diferencias entre show() y fetchall():
# show() muestra el resultado de la consulta en la consola de manera formateada, similar a una tabla, y es útil para obtener una vista rápida de los datos.
# fetchall() devuelve el resultado de la consulta como una lista de tuplas, lo que es útil para manipular los datos programáticamente en Python.

my_dictionary = {}
my_dictionary["test_df"] = pd.DataFrame.from_dict({"i": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]})
duckdb.register("test_df_view", my_dictionary["test_df"])
print(duckdb.sql("SELECT * FROM test_df_view").fetchall())