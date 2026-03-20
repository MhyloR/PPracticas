# views/graficos.py
import streamlit as st
import random
from pathlib import Path
from datetime import date

from core.catalog import cargar_catalogo
from core.filters import guardar_seleccion_filtros, FiltroError
from core.exporter import DataFrameExporter, build_export_base_name

# Import de TU API (usa exactamente lo que tienes en el proyecto)
from Read.Api import get_df_unificado


# =========================================
# Helpers
# =========================================
def to_yyyy_mm_dd(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def sync_from_id(by_id: dict):
    """
    Cuando se selecciona un ID:
    - se guarda simem_dataset_id
    - se setea automáticamente el nombre asociado
    """
    selected_id = (st.session_state.get("simem_dataset_id_select") or "").strip()
    if selected_id:
        st.session_state["simem_dataset_id"] = selected_id
        st.session_state["simem_dataset_name"] = by_id.get(selected_id, "")
        st.session_state["simem_dataset_name_select"] = by_id.get(selected_id, "")
    else:
        st.session_state["simem_dataset_id"] = ""
        st.session_state["simem_dataset_name"] = ""
        st.session_state["simem_dataset_name_select"] = ""


def sync_from_name(by_name: dict):
    """
    Cuando se selecciona un nombre:
    - se guarda simem_dataset_name
    - se setea automáticamente el ID asociado
    """
    selected_name = (st.session_state.get("simem_dataset_name_select") or "").strip()
    if selected_name:
        st.session_state["simem_dataset_name"] = selected_name
        st.session_state["simem_dataset_id"] = by_name.get(selected_name, "")
        st.session_state["simem_dataset_id_select"] = by_name.get(selected_name, "")
    else:
        st.session_state["simem_dataset_name"] = ""
        st.session_state["simem_dataset_id"] = ""
        st.session_state["simem_dataset_id_select"] = ""


# =========================================
# Render
# =========================================
def render():
    col_filtros, col_grafica = st.columns([1, 2], gap="large")

    # =======================
    # Panel de filtros
    # =======================
    with col_filtros:
        st.markdown('<div class="section-title">Configuración</div>', unsafe_allow_html=True)

        # -------- Fuente de datos
        st.markdown(
            '<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fuente de datos</p>',
            unsafe_allow_html=True
        )
        fuente = st.selectbox(
            "Fuente de datos",
            ["SIMEM", "Archivo Plano"],
            label_visibility="collapsed",
            key="fuente_datos"
        )

        # =======================
        # SIMEM
        # =======================
        if fuente == "SIMEM":
            ruta_json = Path("Storage") / "Nombre de variables del catálogo_filtrado.json"
            catalogo = cargar_catalogo(ruta_json)

            if "error" in catalogo:
                st.error(catalogo["error"])
                return

            by_id = catalogo["by_id"]       # {id: nombre}
            by_name = catalogo["name_to_id"] if "name_to_id" in catalogo else {v: k for k, v in by_id.items()}

            id_options = [""] + sorted(by_id.keys())            # SOLO IDs
            name_options = [""] + sorted(by_name.keys())        # SOLO NOMBRES

            c1, c2 = st.columns(2)

            # -------- idDataset (solo IDs)
            with c1:
                st.markdown(
                    '<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">idDataset</p>',
                    unsafe_allow_html=True
                )
                st.selectbox(
                    "idDataset",
                    options=id_options,
                    key="simem_dataset_id_select",
                    label_visibility="collapsed",
                    help="Escribe para buscar por ID del dataset",
                    on_change=sync_from_id,
                    args=(by_id,)
                )

            # -------- nombreConjuntoDatos (solo nombres)
            with c2:
                st.markdown(
                    '<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">nombreConjuntoDatos</p>',
                    unsafe_allow_html=True
                )
                st.selectbox(
                    "nombreConjuntoDatos",
                    options=name_options,
                    key="simem_dataset_name_select",
                    label_visibility="collapsed",
                    help="Escribe para buscar por nombre del conjunto",
                    on_change=sync_from_name,
                    args=(by_name,)
                )

            # -------- Fechas
            st.markdown(
                '<p style="font-weight:600;color:var(--accent);margin:var(--m) 0 var(--xs) 0;">Fecha Inicio</p>',
                unsafe_allow_html=True
            )
            fecha_inicio = st.date_input("fecha_inicio", label_visibility="collapsed")

            st.markdown(
                '<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Fin</p>',
                unsafe_allow_html=True
            )
            fecha_fin = st.date_input("fecha_fin", label_visibility="collapsed")

            # -------- Botones
            if st.button("Consultar y guardar (SIMEM)", use_container_width=True):
                dataset_id = (st.session_state.get("simem_dataset_id") or "").strip()

                if not dataset_id:
                    st.error("Debes seleccionar un idDataset.", icon="⚠️")
                    st.stop()

                if fecha_inicio > fecha_fin:
                    st.error("La fecha inicio no puede ser mayor que la fecha fin.", icon="⚠️")
                    st.stop()

                ini = to_yyyy_mm_dd(fecha_inicio)
                fin = to_yyyy_mm_dd(fecha_fin)

                with st.spinner(f"Consultando SIMEM… {dataset_id} | {ini} → {fin}"):
                    try:
                        result = get_df_unificado(
                            dataset_id=dataset_id,
                            fecha_inicio=ini,
                            fecha_final=fin,
                            include_namecolumns=False
                        )

                        df = result.get("dataframe")

                        if df is None or df.empty:
                            st.info("Consulta OK, pero sin datos para el rango dado.", icon="ℹ️")
                            return

                        base_name = build_export_base_name(dataset_id, ini, fin)
                        exporter = DataFrameExporter("Storage", base_name)
                        csv_path, json_path = exporter.export(df)

                        st.success(
                            f"Consulta OK ✅",
                            icon="✅"
                        )

                    except Exception as e:
                        st.error(f"Error consultando SIMEM: {e}", icon="❌")

        # =======================
        # Archivo Plano
        # =======================
        else:
            st.file_uploader(
                "Cargar archivo",
                type=["csv", "json"],
                accept_multiple_files=False
            )

    # =======================
    # Panel de gráfica (placeholder)
    # =======================
    with col_grafica:
        st.markdown('<div class="section-title">Visualización</div>', unsafe_allow_html=True)
        st.info("La visualización se activará cuando conectemos el DataFrame real.")
