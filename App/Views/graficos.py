# views/graficos.py
import streamlit as st
import random
from pathlib import Path
from core.catalog import cargar_catalogo

def _sync_from_id(by_id, to_display_by_name):
    disp = st.session_state.get("simem_dataset_id_select", "")
    if disp:
        selected_id = disp.split(" — ")[0].strip()
        selected_name = by_id.get(selected_id, "")
        st.session_state["simem_dataset_id"] = selected_id
        st.session_state["simem_dataset_name"] = selected_name
        if selected_name:
            st.session_state["simem_dataset_name_select"] = to_display_by_name[selected_name]
    else:
        st.session_state["simem_dataset_id"] = ""
        st.session_state["simem_dataset_name"] = ""
        st.session_state["simem_dataset_name_select"] = ""

def _sync_from_name(by_name, to_display_by_id):
    disp = st.session_state.get("simem_dataset_name_select", "")
    if disp:
        selected_name = disp.split(" — ")[0].strip()
        selected_id = by_name.get(selected_name, "")
        st.session_state["simem_dataset_name"] = selected_name
        st.session_state["simem_dataset_id"] = selected_id
        if selected_id:
            st.session_state["simem_dataset_id_select"] = to_display_by_id[selected_id]
    else:
        st.session_state["simem_dataset_name"] = ""
        st.session_state["simem_dataset_id"] = ""
        st.session_state["simem_dataset_id_select"] = ""

def render():
    col_filtros, col_grafica = st.columns([1, 2], gap="large")

    # ---- Panel de filtros
    with col_filtros:
        st.markdown('<div class="section-title">Configuración</div>', unsafe_allow_html=True)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fuente de datos</p>', unsafe_allow_html=True)
        fuente = st.selectbox("Fuente de datos", ["SIMEM", "Archivo Plano"], label_visibility="collapsed", key="fuente_datos")

        if fuente == "SIMEM":
            ruta_json = Path("Storage") / "Nombre de variables del catálogo_filtrado.json"
            catalogo = cargar_catalogo(ruta_json)

            if "error" in catalogo:
                st.error(catalogo["error"])
                if "keys_detectadas" in catalogo:
                    st.info(f"Claves detectadas: {', '.join(catalogo['keys_detectadas'])}")
            else:
                by_id, by_name = catalogo["by_id"], catalogo["by_name"]
                display_id   = [""] + catalogo["display_id"]
                display_name = [""] + catalogo["display_name"]

                to_display_by_id   = {idv: (f"{idv} — {nm}" if nm else idv) for idv, nm in by_id.items()}
                to_display_by_name = {nm: (f"{nm} — {idv}" if idv else nm) for nm, idv in by_name.items()}

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">idDataset</p>', unsafe_allow_html=True)
                    st.selectbox(
                        "idDataset",
                        options=display_id,
                        index=(display_id.index(st.session_state["simem_dataset_id_select"])
                               if st.session_state["simem_dataset_id_select"] in display_id else 0),
                        key="simem_dataset_id_select",
                        label_visibility="collapsed",
                        help="Escribe para buscar por ID o parte del nombre",
                        on_change=_sync_from_id, args=(by_id, to_display_by_name,)
                    )
                with c2:
                    st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">nombreConjuntoDatos</p>', unsafe_allow_html=True)
                    st.selectbox(
                        "nombreConjuntoDatos",
                        options=display_name,
                        key="simem_dataset_name_select",
                        label_visibility="collapsed",
                        on_change=_sync_from_name,
                        args=(by_name, to_display_by_id,)
                    )

        else:
            st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Cargar archivo</p>', unsafe_allow_html=True)
            st.file_uploader(
                "Selecciona un archivo",
                type=["csv", "json"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                help="Formatos permitidos: CSV o Json",
                key="archivo_plano"
            )

        # Fechas
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Inicio</p>', unsafe_allow_html=True)
        st.date_input("fecha de consulta", label_visibility="collapsed", key="fecha_inicio")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Fin</p>', unsafe_allow_html=True)
        st.date_input("fecha de consulta1", label_visibility="collapsed", key="fecha_fin")

        # Filtro
        with st.container(border=True, key="filtro"):
            st.markdown("### Filtro")
            opciones_filtro = ["Etapa", "Código Agente", "Actividad", "Código SIC Agente", "Versión"]
            seleccion = st.radio(
                label="Selecciona un filtro",
                options=opciones_filtro,
                index=opciones_filtro.index(st.session_state["filtro_sel"]),
                label_visibility="collapsed",
                horizontal=False,
                key="filtro_radio",
            )
            st.session_state["filtro_sel"] = seleccion
            st.markdown(f"<div class='muted'>Opción actual: {st.session_state['filtro_sel']}</div>", unsafe_allow_html=True)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Valor de filtro</p>', unsafe_allow_html=True)
        st.selectbox("Valor del filtro", ["001", "002", "003"], label_visibility="collapsed", key="valor_filtro")

        # Botones
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Reiniciar", use_container_width=True):
                st.session_state["datos_cargados"] = False
                st.session_state["mostrar_grafica"] = False
                st.session_state["filtros_aplicados"] = []
                st.session_state["simem_dataset_id"] = ""
                st.session_state["simem_dataset_name"] = ""
                st.session_state["simem_dataset_id_select"] = ""
                st.session_state["simem_dataset_name_select"] = ""
        with b2:
            if st.button("Cargar datos", use_container_width=True):
                st.session_state["datos_cargados"] = True
                st.session_state["filtros_aplicados"].append(f"{st.session_state['filtro_sel']}: {st.session_state['valor_filtro']}")
        with b3:
            if st.button("Generar gráfica", use_container_width=True, disabled=not st.session_state["datos_cargados"]):
                if st.session_state["datos_cargados"]:
                    st.session_state["mostrar_grafica"] = True

    # ---- Panel de gráfica
    with col_grafica:
        st.markdown('<div class="section-title">Visualización</div>', unsafe_allow_html=True)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE X</p>', unsafe_allow_html=True)
        st.selectbox("EJE X", ["Tiempo", "Fecha", "Periodo"], label_visibility="collapsed", key="eje_x")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE Y</p>', unsafe_allow_html=True)
        st.selectbox("EJE Y", ["Valor", "Promedio", "Índice"], label_visibility="collapsed", key="eje_y")

        if st.session_state["mostrar_grafica"]:
            data_fake = {
                "Tomate": [random.randint(0, 70) for _ in range(100)],
                "Cebolla": [random.randint(0, 70) for _ in range(100)],
            }
            st.line_chart(data_fake, height=300)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Filtros aplicados</p>', unsafe_allow_html=True)
        st.write(st.session_state["filtros_aplicados"])