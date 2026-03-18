import streamlit as st
import random

# =========================
# Configuración general
# =========================
st.set_page_config(page_title="Monitor de Variables SIMEM", page_icon="🟪", layout="wide")

# =========================
# Paleta, espaciados y radios (global)
# =========================
ACCENT      = "#571D92"
SIDEBAR_BG  = "#6D59D1FF"
APP_BG      = "#E6E6E6"
PANEL_BG    = "#00966C"
TEXT        = "#E7E9EE"
TEXT_DARK   = "#000000"
MUTED       = "#9AA0AA"
RADIUS      = "12px"

# Colores del cuadro (edita aquí y afecta a todos los date_input)
INPUT_BG    = "#FFFFFF"   # fondo del cuadro
INPUT_TEXT  = "#111827"   # texto
INPUT_BORDER= "#D1D5DB"   # borde visible (interno)
INPUT_FOCUS = "#6366F1"   # color de foco e ícono

SPACE_XS="6px"; 
SPACE_S="10px"; 
SPACE_M="16px"; 
SPACE_L="20px"; 
SPACE_XL="28px"

# =========================
# Estilos globales
# =========================
st.markdown(f"""
<style>
:root {{
  --accent:{ACCENT}; --sidebar-bg:{SIDEBAR_BG}; --app-bg:{APP_BG}; --panel-bg:{PANEL_BG};
  --text:{TEXT}; --text-dark:{TEXT_DARK}; --muted:{MUTED}; --radius:{RADIUS};
  --xs:{SPACE_XS}; --s:{SPACE_S}; --m:{SPACE_M}; --l:{SPACE_L}; --xl:{SPACE_XL};
  --input-bg:{INPUT_BG}; --input-text:{INPUT_TEXT}; --input-border:{INPUT_BORDER}; --input-focus:{INPUT_FOCUS};
}}

[data-testid="stAppViewContainer"]{{ background-color: var(--app-bg); }}
.main .block-container{{ padding: var(--l) !important; }}

[data-testid="stSidebar"]{{ background-color: var(--sidebar-bg) !important; padding: var(--l) var(--m) !important; }}
[data-testid="stSidebar"] *{{ color:#FFFFFF !important; }}
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stSelectbox>div>div>div,
[data-testid="stSidebar"] .stDateInput>div>div>input{{ background-color:#FFFFFF !important; color:#000 !important; border-radius:6px; }}
[data-testid="stSidebar"] button[kind="secondary"]{{ color:var(--sidebar-bg) !important; background-color:#FFFFFF !important; border:1px solid #FFFFFF33 !important; border-radius:8px; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{{ color:#FFFFFF !important; margin:var(--m) 0; }}

.app-header{{ background-color:#5b1fa6; padding:var(--m); border-radius:8px; color:#FFFFFF; text-align:center; font-size:20px; font-weight:800; margin:0 0 var(--l) 0; }}
.section-title{{ font-weight:700; font-size:28px; color:var(--accent); margin:0 0 var(--s) 0; }}
.card{{ border:3px solid var(--accent); background-color:#F4F3FA; border-radius:var(--radius); padding:var(--l); min-height:300px; margin:0; }}
.card h3{{ color:var(--accent); margin:0 0 var(--s) 0; }}
.card p{{ color:var(--text-dark); margin:0; }}

.st-key-filtro{{ border-radius:var(--radius); background:var(--panel-bg); padding:var(--m) var(--l); box-sizing:border-box; margin:0; }}
.st-key-filtro h3{{ margin:0 0 var(--s) 0; font-weight:800; color:var(--text); letter-spacing:.2px; }}
.st-key-filtro h1 a,.st-key-filtro h2 a,.st-key-filtro h3 a{{ display:none !important; }}
.st-key-filtro .stRadio ul{{ list-style:none; margin:0; padding-left:0; }}
.st-key-filtro .stRadio li::marker{{ content:''; }}
.st-key-filtro .stRadio div[role="radiogroup"]>label{{ display:grid; grid-template-columns:18px 1fr; align-items:center; column-gap:10px; padding:6px 4px; border-radius:8px; line-height:1.25; color:var(--text); }}
.st-key-filtro .stRadio div[role="radiogroup"]>label:hover{{ background:rgba(255,255,255,0.06); }}
.st-key-filtro .muted{{ color:var(--muted); font-size:.9rem; margin-top:var(--s); }}

.css-ocqkz7, .css-1kyxreq{{ gap:var(--l) !important; }}

/* === DATE INPUT: dejar solo borde interno === */
[data-testid="stDateInput"] [data-baseweb="input"]{{  /* wrapper externo sin borde */
  background: var(--input-bg) !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 10px !important;
}}
[data-testid="stDateInput"] input{{                  /* único borde visible */
  background: var(--input-bg) !important;
  color: var(--input-text) !important;
  border: 1px solid var(--input-border) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  box-shadow: none !important;
}}
[data-testid="stDateInput"] [data-baseweb="input"]:focus-within,
[data-testid="stDateInput"] input:focus{{
  border-color: var(--input-focus) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.25) !important;
  outline: none !important;
}}
[data-testid="stDateInput"] svg{{ color: var(--input-focus) !important; }}
</style>
""", unsafe_allow_html=True)

# =========================
# Estado global
# =========================
st.session_state.setdefault("datos_cargados", False)
st.session_state.setdefault("filtros_aplicados", [])
st.session_state.setdefault("mostrar_grafica", False)
st.session_state.setdefault("filtro_sel", "Etapa")

# =========================
# Header
# =========================
st.markdown('<div class="app-header">MONITOR DE VARIABLES SIMEM</div>', unsafe_allow_html=True)

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.title("Equipo Analítica")
    vista = st.radio("Menú", ["Documentación", "Generación de gráficos", "Outliers"])

# =========================
# VISTA: Documentación
# =========================
if vista == "Documentación":
    st.markdown('<h2 style="color:#000;margin:0 0 var(--s) 0;">hola</h2>', unsafe_allow_html=True)
    st.markdown("""
      <div class="card">
        <h3>Heading</h3>
        <p>Aqui va a ir una cantidad de texto pero es mucha dejeme decirle</p>
      </div>
    """, unsafe_allow_html=True)

# =========================
# VISTA: Generación de gráficos
# =========================
elif vista == "Generación de gráficos":
    col_filtros, col_grafica = st.columns([1, 2], gap="large")

    # Panel de filtros
    with col_filtros:
        st.markdown('<div class="section-title">Configuración</div>', unsafe_allow_html=True)

        # Fuente de datos
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fuente de datos</p>', unsafe_allow_html=True)
        fuente = st.selectbox("Fuente de datos", ["SIMEM", "Archivo Plano"], label_visibility="collapsed", key="fuente_datos")

        # >>> Interacción condicional solicitada <<<
        if fuente == "SIMEM":
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Dataset ID</p>', unsafe_allow_html=True)
                dataset_id = st.text_input("Dataset ID", placeholder="Ej: 12345-abc", label_visibility="collapsed", key="simem_dataset_id")
            with c2:
                st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Nombre de conjunto de datos</p>', unsafe_allow_html=True)
                dataset_name = st.text_input("Nombre de conjunto de datos", placeholder="Ej: SIMEM - Producción", label_visibility="collapsed", key="simem_dataset_name")
        else:
            st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Cargar archivo</p>', unsafe_allow_html=True)
            archivo_plano = st.file_uploader(
                "Selecciona un archivo",
                type=["csv", "xlsx", "xls", "parquet"],
                accept_multiple_files=False,
                label_visibility="collapsed",
                help="Formatos permitidos: CSV, Excel (XLS/XLSX) o Parquet",
                key="archivo_plano"
            )

        # Fechas
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Inicio</p>', unsafe_allow_html=True)
        fecha_inicio  = st.date_input("fecha de consulta", label_visibility="collapsed", key="fecha_inicio")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Fin</p>', unsafe_allow_html=True)
        fecha_fin  = st.date_input("fecha de consulta1", label_visibility="collapsed", key="fecha_fin")

        # Panel de filtro
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
        valor_filtro = st.selectbox("Valor del filtro", ["001", "002", "003"], label_visibility="collapsed", key="valor_filtro")

        # Botones
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("Reiniciar", use_container_width=True):
                st.session_state["datos_cargados"] = False
                st.session_state["mostrar_grafica"] = False
                st.session_state["filtros_aplicados"] = []
        with b2:
            if st.button("Cargar datos", use_container_width=True):
                st.session_state["datos_cargados"] = True
                st.session_state["filtros_aplicados"].append(f"{seleccion}: {valor_filtro}")
        with b3:
            if st.button("Generar gráfica", use_container_width=True):
                if st.session_state["datos_cargados"]:
                    st.session_state["mostrar_grafica"] = True

    # Panel de gráfica
    with col_grafica:
        st.markdown('<div class="section-title">Visualización</div>', unsafe_allow_html=True)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE X</p>', unsafe_allow_html=True)
        eje_x = st.selectbox("EJE X", ["Tiempo", "Fecha", "Periodo"], label_visibility="collapsed")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE Y</p>', unsafe_allow_html=True)
        eje_y = st.selectbox("EJE Y", ["Valor", "Promedio", "Índice"], label_visibility="collapsed")

        if st.session_state["mostrar_grafica"]:
            data_fake = {
                "Tomate": [random.randint(0, 10) for _ in range(5)],
                "Cebolla": [random.randint(0, 10) for _ in range(5)],
            }
            st.line_chart(data_fake, height=300)

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Filtros aplicados</p>', unsafe_allow_html=True)
        st.write(st.session_state["filtros_aplicados"])

# =========================
# VISTA: Outliers
# =========================
else:
    st.markdown('<div class="section-title">Outliers</div>', unsafe_allow_html=True)
    st.write("Outliers detectados: 0")
