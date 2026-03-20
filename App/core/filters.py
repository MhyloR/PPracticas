# core/filters.py
from __future__ import annotations
import streamlit as st
from datetime import date

class FiltroError(Exception):
    """Error de validación de filtros (dataset y fechas)."""
    pass

def _to_yyyy_mm_dd(d: date) -> str:
    """Formatea datetime.date -> 'YYYY-MM-DD'."""
    return d.strftime("%Y-%m-%d")

def guardar_seleccion_filtros(dataset_id: str, fecha_inicio: date, fecha_fin: date) -> dict:
    """
    Valida y guarda en session_state:
      - filtro_dataset_id
      - filtro_fecha_inicio (YYYY-MM-DD)
      - filtro_fecha_final  (YYYY-MM-DD)
      - filtros_consulta    (dict resumen)
    Devuelve el dict de filtros guardados.
    """
    # Validaciones
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        raise FiltroError("Debes seleccionar un idDataset válido.")

    if not isinstance(fecha_inicio, date) or not isinstance(fecha_fin, date):
        raise FiltroError("Debes seleccionar la Fecha Inicio y la Fecha Fin.")

    ini = _to_yyyy_mm_dd(fecha_inicio)
    fin = _to_yyyy_mm_dd(fecha_fin)

    if ini > fin:
        raise FiltroError("La Fecha Inicio no puede ser mayor que la Fecha Fin.")

    # Persistencia en session_state
    st.session_state["filtro_dataset_id"]   = dataset_id
    st.session_state["filtro_fecha_inicio"] = ini
    st.session_state["filtro_fecha_final"]  = fin

    filtros = {"dataset_id": dataset_id, "fecha_inicio": ini, "fecha_final": fin}
    st.session_state["filtros_consulta"] = filtros
    return filtros