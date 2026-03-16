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
# Estilos globales (fondo página y sidebar)
# -----------------------
st.markdown("""
    <style>
    /* Fondo del contenedor principal de la app */
    [data-testid="stAppViewContainer"] {
        background-color: #E6E6E6;
    }

    /* Fondo del sidebar */
    [data-testid="stSidebar"] {
        background-color: #672F9C !important;
    }

    /* Texto dentro del sidebar en blanco para contraste */
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* Color del label seleccionado en radio/select dentro del sidebar */
    [data-testid="stSidebar"] .st-bx, 
    [data-testid="stSidebar"] .st-bz,
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }

    /* Inputs del sidebar con borde y fondo legible */
    [data-testid="stSidebar"] .stTextInput>div>div>input,
    [data-testid="stSidebar"] .stSelectbox>div>div>div,
    [data-testid="stSidebar"] .stDateInput>div>div>input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 6px;
    }

    /* Botones en el sidebar con bordes visibles */
    [data-testid="stSidebar"] button[kind="secondary"] {
        color: #672F9C !important;
        background-color: #FFFFFF !important;
        border: 1px solid #FFFFFF33 !important;
        border-radius: 8px;
    }

    /* Ajuste de títulos en sidebar para buena jerarquía visual */
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

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
        color:White;
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
    
    st.markdown("""
    <h2>
        <span style="color:#000000;">hola</span>
    </h2>
    """, unsafe_allow_html=True)


    st.markdown("""
        <div style="
            border: 3px solid #571D92;
            background-color: #F4F3FA;
            border-radius: 12px;
            padding: 20px;
            min-height: 300px;
        ">
            <h3 style="color:#571D92; margin-top:0;">
                Heading
            </h3>
            <p style="color:#000000;">
                Info general de la página y que tales
            </p>
        </div>
    """, unsafe_allow_html=True)


# =======================
# VISTA: Generación de gráficos
# =======================
if vista == "Generación de gráficos":

    col_filtros, col_grafica = st.columns([1, 2])

    # -----------------------
    # Panel de filtros
    # -----------------------
    with col_filtros:
        st.markdown("""
            <div style="
                font-weight:600;
                font-size:28px;
                color:#571D92;
                margin-bottom:10px;
            ">
                Configuración
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
            <p style="font-weight:600; color:#571D92; margin-bottom:4px;">
                Fuente de datos
            </p>
        """, unsafe_allow_html=True)

        fuente = st.selectbox(
            "Fuente de datos",  
            ["SIMEM", "Archivo Plano"],
            label_visibility="collapsed"
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
        st.markdown("""
            <div style="
                font-weight:600;
                font-size:28px;
                color:#571D92;
                margin-bottom:10px;
            ">
                Visualización
            </div>
        """, unsafe_allow_html=True)

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