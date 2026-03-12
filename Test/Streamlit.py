import streamlit as st
import random

# -----------------------
# Configuración general
# -----------------------
st.set_page_config(
    page_title="Monitor de Variables SIMEM",
    layout="wide"
)

# -----------------------
# Inicializar estado
# -----------------------
if "datos_cargados" not in st.session_state:
    st.session_state.datos_cargados = False

if "filtros_aplicados" not in st.session_state:
    st.session_state.filtros_aplicados = []

if "mostrar_grafica" not in st.session_state:
    st.session_state.mostrar_grafica = False


# -----------------------
# Header
# -----------------------
st.markdown(
    """
    <div style="
        background-color:#5b1fa6;
        padding:15px;
        border-radius:5px;
        color:white;
        text-align:center;
        font-size:20px;
        font-weight:bold;">
        MONITOR DE VARIABLES SIMEM
    </div>
    """,
    unsafe_allow_html=True
)

st.write("")

# -----------------------
# Sidebar (Navegación)
# -----------------------
with st.sidebar:
    st.title("Equipo Analítica")

    vista = st.radio(
        "Menú",
        ["Documentación", "Generación de gráficos", "Outliers"]
    )

# =======================
# VISTA: Documentación
# =======================
if vista == "Documentación":
    st.header("Hola")
    st.subheader("Heading")
    st.write("Info general de la página y que tales")

# =======================
# VISTA: Generación de gráficos
# =======================
if vista == "Generación de gráficos":

    col_filtros, col_grafica = st.columns([1, 2])

    # -----------------------
    # Panel de filtros
    # -----------------------
    with col_filtros:
        st.subheader("Configuración")

        fuente = st.selectbox(
            "Fuente",
            ["SIMEM", "Archivo Plano"]
        )

        variable = st.selectbox(
            "Variable",
            ["Global", "Global flexible"]
        )

        fecha = st.date_input("Fecha")

        filtro_principal = st.radio(
            "Filtro",
            ["Etapa", "Código Agente", "Actividad", "Código SIC Agente", "Versión"]
        )

        valor_filtro = st.selectbox(
            "Valor del filtro",
            ["001", "002", "003"]
        )

        # -----------------------
        # Botones
        # -----------------------
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            if st.button("Reiniciar"):
                st.session_state.datos_cargados = False
                st.session_state.mostrar_grafica = False
                st.session_state.filtros_aplicados = []

        with col_btn2:
            if st.button("Cargar datos"):
                st.session_state.datos_cargados = True
                st.session_state.filtros_aplicados.append(
                    f"{filtro_principal}: {valor_filtro}"
                )

        with col_btn3:
            if st.button("Generar gráfica"):
                if st.session_state.datos_cargados:
                    st.session_state.mostrar_grafica = True

    # -----------------------
    # Panel de gráfica
    # -----------------------
    with col_grafica:
        st.subheader("Visualización")

        eje_x = st.selectbox("EJE X", ["Tiempo", "Fecha", "Periodo"])
        eje_y = st.selectbox("EJE Y", ["Valor", "Promedio", "Índice"])

        if st.session_state.mostrar_grafica:
            data_fake = {
                "serie_1": [random.randint(0, 10) for _ in range(5)],
                "serie_2": [random.randint(0, 10) for _ in range(5)]
            }
            st.line_chart(data_fake)

        st.write("Filtros aplicados:")
        st.write(st.session_state.filtros_aplicados)

# =======================
# VISTA: Outliers
# =======================
if vista == "Outliers":
    st.header("Outliers")
    st.write("Outliers detectados: 0")
