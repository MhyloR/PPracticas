from click import Path
import pandas as pd
from Processing.deleite import DirectoryCleaner
from Read.Api import get_df_unificado
from Read.FFlat import load_to_dataframe
from Processing.AtribSelect import ejecutar_interactivo
from Processing.Divide import Separacion
from datetime import date
from dateutil.relativedelta import relativedelta
from Processing.GetColumns import obtener_columnas_df   # viene con python‑dateutil
from Processing.Save import DataFrameExporter
    
today = date.today()
three_months_ago = today - relativedelta(months=3)

selection = input('Will you work with DataSets or Flat Files? (D/F): ').lower()

if selection == "d":
    # Dataset request
    input_set = input("Enter the dataset ID to process: ")

    print("Please enter the date range to process. If nothing is entered, the last three months of data will be used.")
    start_date = input("Enter the start date (YYYY-MM-DD): ")

    if not start_date:
        start_date = three_months_ago.isoformat()

    print("Start date:", start_date)
    end_date = input("Enter the end date (YYYY-MM-DD): ")

    if not end_date:
        end_date = today.isoformat()

    print("End date:", end_date)

    result = get_df_unificado(
        dataset_id=input_set,
        fecha_inicio=start_date,
        fecha_final=end_date,
        include_namecolumns=False  # uses df.columns (does not query endpoint)
    )

    df = result["dataframe"]
    namecolumns = result["namecolumns"]
    file_name = f"filtered_data_{input_set}_{start_date}_to_{end_date}"
    info = DataFrameExporter(base_path="Storage", file_name=file_name)
    csv_path, json_path = info.export(df)

if selection == "f":
    print("Loading file...")
    file_path = input("Enter the path to the flat file: ")
    df = load_to_dataframe(file_path)
    namecolumns = obtener_columnas_df(df)

data = []

# Yes/no helper for interactive input
def yes_no(prompt: str) -> bool:
    while True:
        r = input(f"{prompt} (y/n): ").strip().lower()
        if r in ("y", "n"):
            return r == "y"
        print("→ Please respond with 'y' or 'n'.")

continue_filtering = True

# Filtering stage
while continue_filtering:
    print("\n=== New Filtering Round ===")
    df_filtered = ejecutar_interactivo(df)

    while yes_no("Add another filter on the current result?"):
        df_filtered = ejecutar_interactivo(df_filtered)

    data.append(df_filtered.copy())
    print("Filtered result saved.")

    continue_filtering = yes_no("Start filtering another attribute (restart from original df)?")

# Export stage
for j, item in enumerate(data):
    df_filtered = item
    if df_filtered is None or df_filtered.empty:
        print(f"[WARN] DataFrame {j} is empty. Skipping.")
        continue

    file_name = f"filtered_data_{j:03d}"
    exporter = DataFrameExporter(base_path="outputs", file_name=file_name)

    try:
        csv_path, json_path = exporter.export(df_filtered)
        print(f"DataFrame {j} saved as CSV:  {csv_path}")
        print(f"DataFrame {j} saved as JSON: {json_path}")
    except Exception as e:
        print(f"[ERROR] Could not export DataFrame {j}: {e}")

delete = input('Do u want to clean the output directory? (y/n): ').lower()
if delete == "y":
    cleaner = DirectoryCleaner("outputs")
    cleaner.delete_all(
        recursive=True,
        exclude=[],
        dry_run=False,
        verbose=True
    )
else:
    pass

# Separation stage
sep = []
for i in range(len(data)):
    df_filtered = data[i]
    df_general, meta = Separacion(namecolumns, df_filtered)
    sep.append(df_general)

# Scaling factor
scaling_factor = float(input("Enter the scaling factor for the second column: "))

# Apply scaling and cleanup
for i in range(len(sep)):
    df_general = sep[i].copy()
    df_general.iloc[:, 0] = pd.to_datetime(df_general.iloc[:, 0], errors="coerce")
    df_general = df_general.dropna(subset=[df_general.columns[0]])
    df_general = df_general.sort_values(by=df_general.columns[0])
    df_general.iloc[:, 1] = df_general.iloc[:, 1].div(float(scaling_factor))
    sep[i] = df_general


