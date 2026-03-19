# core/state.py
import streamlit as st

def ensure_defaults():
    st.session_state.setdefault("datos_cargados", False)
    st.session_state.setdefault("filtros_aplicados", [])
    st.session_state.setdefault("mostrar_grafica", False)
    st.session_state.setdefault("filtro_sel", "Etapa")

    # SIMEM (type-ahead sincronizado)
    st.session_state.setdefault("simem_dataset_id", "")
    st.session_state.setdefault("simem_dataset_name", "")
    st.session_state.setdefault("simem_dataset_id_select", "")
    st.session_state.setdefault("simem_dataset_name_select", "")