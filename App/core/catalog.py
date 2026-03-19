# core/catalog.py
import json, os
from typing import Dict, Any
from pathlib import Path
import streamlit as st

CANDIDATES_ID   = ["idDataset", "dataset_id", "id", "codigo", "code", "IdDataset"]
CANDIDATES_NAME = ["nombreConjuntoDatos", "nombre", "dataset_name", "name", "NombreConjuntoDatos"]

@st.cache_data(show_spinner=False)
def cargar_catalogo(ruta_json: str|os.PathLike) -> Dict[str, Any]:
    p = Path(ruta_json)
    if not p.exists():
        return {"error": f"No se encontró el archivo: {p.as_posix()}"}

    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Si viene como dict, intenta extraer lista de dicts
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and all(isinstance(i, dict) for i in v):
                data = v
                break

    if not isinstance(data, list) or not all(isinstance(i, dict) for i in data):
        return {"error": "El JSON no contiene una lista de objetos usable."}

    all_keys = set().union(*[d.keys() for d in data]) if data else set()
    id_key   = next((k for k in CANDIDATES_ID   if k in all_keys), None)
    name_key = next((k for k in CANDIDATES_NAME if k in all_keys), None)

    if not id_key or not name_key:
        return {"error": "No se detectaron las claves de ID/Nombre en el JSON.",
                "keys_detectadas": sorted(list(all_keys))}

    by_id, by_name = {}, {}
    for item in data:
        idv = str(item.get(id_key, "")).strip()
        nmv = str(item.get(name_key, "")).strip()
        if idv: by_id[idv] = nmv
        if nmv: by_name[nmv] = idv

    display_id   = [f"{i} — {by_id[i]}" if by_id[i] else i for i in by_id.keys()]
    display_name = [f"{n} — {by_name[n]}" if by_name[n] else n for n in by_name.keys()]

    return {
        "id_key": id_key, "name_key": name_key,
        "by_id": by_id, "by_name": by_name,
        "display_id": display_id, "display_name": display_name,
        "keys_detectadas": sorted(list(all_keys)),
    }