import streamlit as st
import random

# =========================
# Configuración general de la app
# =========================
# Define título de pestaña, ícono y layout ancho
st.set_page_config(page_title="Monitor de Variables SIMEM", page_icon="🟪", layout="wide")

# =========================
# Paleta, espaciados y radios (global) - Design tokens
# =========================
# Variables de diseño reutilizables para colores, textos y radios
ACCENT      = "#571D92"    # Morado principal
SIDEBAR_BG  = "#6D59D1FF"  # Fondo de sidebar
APP_BG      = "#E6E6E6"    # Fondo general de la app
PANEL_BG    = "#00966C"    # Fondo del panel de filtros
TEXT        = "#E7E9EE"    # Texto claro (sobre fondos oscuros)
TEXT_DARK   = "#000000"    # Texto oscuro (sobre fondos claros)
MUTED       = "#9AA0AA"    # Texto deshabilitado/suave
RADIUS      = "12px"       # Radio de borde estándar

# Variables específicas para inputs (TextInput, Selectbox, DateInput, etc.)
INPUT_BG    = "#FFFFFF"    # Fondo del campo
INPUT_TEXT  = "#111827"    # Color de texto del campo
INPUT_BORDER= "#D1D5DB"    # Borde del campo
INPUT_FOCUS = "#6366F1"    # Color de foco/sombra e íconos

# Escala de espaciados
SPACE_XS="6px"; SPACE_S="10px"; SPACE_M="16px"; SPACE_L="20px"; SPACE_XL="28px"

# =========================
# Estilos globales (CSS inyectado)
# =========================
# Aplica el sistema de diseño definindo variables CSS y reglas para:
# - Fondo de app y sidebar
# - Contenedor principal
# - Tarjetas y títulos
# - Panel de filtros estilizado
# - Inputs en sidebar y contenido principal
st.markdown(f"""
<style>
:root {{
  /* Tokens de diseño disponibles como variables CSS */
  --accent:{ACCENT}; --sidebar-bg:{SIDEBAR_BG}; --app-bg:{APP_BG}; --panel-bg:{PANEL_BG};
  --text:{TEXT}; --text-dark:{TEXT_DARK}; --muted:{MUTED}; --radius:{RADIUS};
  --xs:{SPACE_XS}; --s:{SPACE_S}; --m:{SPACE_M}; --l:{SPACE_L}; --xl:{SPACE_XL};
  --input-bg:{INPUT_BG}; --input-text:{INPUT_TEXT}; --input-border:{INPUT_BORDER}; --input-focus:{INPUT_FOCUS};
}}

 /* Fondo general y padding coherente */
[data-testid="stAppViewContainer"]{{ background-color: var(--app-bg); }}
.main .block-container{{ padding: var(--l) !important; }}

 /* Sidebar: fondo morado, texto blanco y controles redondeados */
[data-testid="stSidebar"]{{ background-color: var(--sidebar-bg) !important; padding: var(--l) var(--m) !important; }}
[data-testid="stSidebar"] *{{ color:#FFFFFF !important; }}
[data-testid="stSidebar"] .stTextInput>div>div>input,
[data-testid="stSidebar"] .stSelectbox>div>div>div,
[data-testid="stSidebar"] .stDateInput>div>div>input{{ background-color:#FFFFFF !important; color:#000 !important; border-radius:6px; }}
[data-testid="stSidebar"] button[kind="secondary"]{{ color:var(--sidebar-bg) !important; background-color:#FFFFFF !important; border:1px solid #FFFFFF33 !important; border-radius:8px; }}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{{ color:#FFFFFF !important; margin:var(--m) 0; }}

 /* Encabezado principal y títulos de sección */
.app-header{{ background-color:#5b1fa6; padding:var(--m); border-radius:8px; color:#FFFFFF; text-align:center; font-size:20px; font-weight:800; margin:0 0 var(--l) 0; }}
.section-title{{ font-weight:700; font-size:28px; color:var(--accent); margin:0 0 var(--s) 0; }}

 /* Tarjetas informativas (vista Documentación) */
.card{{ border:3px solid var(--accent); background-color:#F4F3FA; border-radius:var(--radius); padding:var(--l); min-height:300px; margin:0; }}
.card h3{{ color:var(--accent); margin:0 0 var(--s) 0; }}
.card p{{ color:var(--text-dark); margin:0; }}

 /* Panel de filtros con estilo y radios en sus radios */
.st-key-filtro{{ border-radius:var(--radius); background:var(--panel-bg); padding:var(--m) var(--l); box-sizing:border-box; margin:0; }}
.st-key-filtro h3{{ margin:0 0 var(--s) 0; font-weight:800; color:var(--text); letter-spacing:.2px; }}
.st-key-filtro h1 a,.st-key-filtro h2 a,.st-key-filtro h3 a{{ display:none !important; }}
.st-key-filtro .stRadio ul{{ list-style:none; margin:0; padding-left:0; }}
.st-key-filtro .stRadio li::marker{{ content:''; }}
.st-key-filtro .stRadio div[role="radiogroup"]>label{{ display:grid; grid-template-columns:18px 1fr; align-items:center; column-gap:10px; padding:6px 4px; border-radius:8px; line-height:1.25; color:var(--text); }}
.st-key-filtro .stRadio div[role="radiogroup"]>label:hover{{ background:rgba(255,255,255,0.06); }}
.st-key-filtro .muted{{ color:var(--muted); font-size:.9rem; margin-top:var(--s); }}

 /* Separación consistente entre columnas (compatibilidad) */
.css-ocqkz7, .css-1kyxreq{{ gap:var(--l) !important; }}

 /* === DATE INPUT: estilo unificado, sin doble borde, con foco consistente === */
[data-testid="stDateInput"] [data-baseweb="input"]{{  /* wrapper externo sin borde */
  background: var(--input-bg) !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 10px !important;
}}
[data-testid="stDateInput"] input{{                  /* borde visible real del control */
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

 /* === INPUTS EN CONTENIDO PRINCIPAL (NO SIDEBAR): TextInput & Selectbox === */
 /* TextInput: input real */
div[data-testid="stAppViewContainer"] .stTextInput > div > div > input {{
  background: var(--input-bg) !important;   /* blanco */
  color: var(--input-text) !important;      /* texto oscuro */
  border: 1px solid var(--input-border) !important;
  border-radius: 10px !important;
  padding: 10px 14px !important;
  box-shadow: none !important;
}}
 /* TextInput: wrapper baseweb (quita borde externo) */
div[data-testid="stAppViewContainer"] .stTextInput [data-baseweb="input"] {{
  background: var(--input-bg) !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 10px !important;
}}

 /* Selectbox: área visible */
div[data-testid="stAppViewContainer"] .stSelectbox > div > div {{
  background: var(--input-bg) !important;
  color: var(--input-text) !important;
  border: 1px solid var(--input-border) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}}
 /* Selectbox: wrapper baseweb y foco */
div[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"] {{
  background: var(--input-bg) !important;
  border: none !important;
  box-shadow: none !important;
  border-radius: 10px !important;
}}
 /* Foco consistente para inputs y select */
div[data-testid="stAppViewContainer"] .stTextInput [data-baseweb="input"]:focus-within,
div[data-testid="stAppViewContainer"] .stTextInput input:focus,
div[data-testid="stAppViewContainer"] .stSelectbox [data-baseweb="select"]:focus-within {{
  border-color: var(--input-focus) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,.25) !important;
  outline: none !important;
}}
 /* Íconos (chevron del select) */
div[data-testid="stAppViewContainer"] .stSelectbox svg {{
  color: var(--input-focus) !important;
}}

 /* ===== Placeholders más legibles (TextInput) ===== */
 /* Mejora contraste del texto de ejemplo para Dataset ID y Nombre de conjunto */
div[data-testid="stAppViewContainer"] .stTextInput input::placeholder {{
  color: var(--text-dark) !important;   /* usa color de texto oscuro */
  opacity: 0.75 !important;             /* más visible que el default */
}}
/* Compatibilidad cross-browser */
div[data-testid="stAppViewContainer"] .stTextInput input::-webkit-input-placeholder {{
  color: var(--text-dark) !important;
  opacity: 0.75 !important;
}}
div[data-testid="stAppViewContainer"] .stTextInput input::-moz-placeholder {{
  color: var(--text-dark) !important;
  opacity: 0.75 !important;
}}
div[data-testid="stAppViewContainer"] .stTextInput input:-ms-input-placeholder {{
  color: var(--text-dark) !important;
  opacity: 0.75 !important;
}}
div[data-testid="stAppViewContainer"] .stTextInput input::-ms-input-placeholder {{
  color: var(--text-dark) !important;
  opacity: 0.75 !important;
}}
</style>
""", unsafe_allow_html=True)

# =========================
# Estado global de la aplicación
# =========================
# Variables en session_state para controlar flujo e interacción entre vistas
st.session_state.setdefault("datos_cargados", False)   # True cuando el usuario "carga datos"
st.session_state.setdefault("filtros_aplicados", [])   # Historial simple de filtros aplicados
st.session_state.setdefault("mostrar_grafica", False)  # True para mostrar la gráfica
st.session_state.setdefault("filtro_sel", "Etapa")     # Opción seleccionada en el radio de filtro

# =========================
# Header (encabezado de la app)
# =========================
st.markdown('<div class="app-header">MONITOR DE VARIABLES SIMEM</div>', unsafe_allow_html=True)

# =========================
# Sidebar (navegación)
# =========================
# Contiene el cambio de vista de la app
with st.sidebar:
    st.title("Equipo Analítica")
    vista = st.radio("Menú", ["Documentación", "Generación de gráficos", "Outliers"])

# =========================
# VISTA: Documentación
# =========================
# Muestra contenido informativo en una tarjeta
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
# Vista principal de trabajo: filtros a la izquierda, gráfica a la derecha
elif vista == "Generación de gráficos":
    # Dos columnas con proporción 1:2
    col_filtros, col_grafica = st.columns([1, 2], gap="large")

    # ---------- Panel de filtros (columna izquierda) ----------
    with col_filtros:
        st.markdown('<div class="section-title">Configuración</div>', unsafe_allow_html=True)

        # Fuente de datos (SIMEM o Archivo Plano)
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fuente de datos</p>', unsafe_allow_html=True)
        fuente = st.selectbox("Fuente de datos", ["SIMEM", "Archivo Plano"], label_visibility="collapsed", key="fuente_datos")

        # Interacción condicional:
        # - Si SIMEM: aparecen dos TextInput en la misma fila (Dataset ID y Nombre de conjunto)
        # - Si Archivo Plano: aparece un file_uploader para subir un archivo local
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

        # Fechas de consulta (inicio y fin)
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Inicio</p>', unsafe_allow_html=True)
        fecha_inicio  = st.date_input("fecha de consulta", label_visibility="collapsed", key="fecha_inicio")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Fecha Fin</p>', unsafe_allow_html=True)
        fecha_fin  = st.date_input("fecha de consulta1", label_visibility="collapsed", key="fecha_fin")

        # Contenedor con estilo para selección de filtros
        with st.container(border=True, key="filtro"):
            st.markdown("### Filtro")
            opciones_filtro = ["Etapa", "Código Agente", "Actividad", "Código SIC Agente", "Versión"]
            # Radio button para tipo de filtro; sincronizado con session_state
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

        # Selector del valor de filtro (placeholder con valores de muestra)
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Valor de filtro</p>', unsafe_allow_html=True)
        valor_filtro = st.selectbox("Valor del filtro", ["001", "002", "003"], label_visibility="collapsed", key="valor_filtro")

        # Botonera: Reiniciar / Cargar datos / Generar gráfica
        b1, b2, b3 = st.columns(3)
        with b1:
            # Limpia estados (como si reiniciaras la vista)
            if st.button("Reiniciar", use_container_width=True):
                st.session_state["datos_cargados"] = False
                st.session_state["mostrar_grafica"] = False
                st.session_state["filtros_aplicados"] = []
        with b2:
            # Marca que los datos "se cargaron" y guarda la combinación de filtro elegida
            if st.button("Cargar datos", use_container_width=True):
                st.session_state["datos_cargados"] = True
                st.session_state["filtros_aplicados"].append(f"{seleccion}: {valor_filtro}")
        with b3:
            # Habilita la gráfica si antes "cargaste datos"
            if st.button("Generar gráfica", use_container_width=True):
                if st.session_state["datos_cargados"]:
                    st.session_state["mostrar_grafica"] = True

    # ---------- Panel de gráfica (columna derecha) ----------
    with col_grafica:
        st.markdown('<div class="section-title">Visualización</div>', unsafe_allow_html=True)

        # Selectores de ejes (aún no conectan con lógica de datos reales)
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE X</p>', unsafe_allow_html=True)
        eje_x = st.selectbox("EJE X", ["Tiempo", "Fecha", "Periodo"], label_visibility="collapsed")

        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">EJE Y</p>', unsafe_allow_html=True)
        eje_y = st.selectbox("EJE Y", ["Valor", "Promedio", "Índice"], label_visibility="collapsed")

        # Gráfica de ejemplo: datos aleatorios hasta conectar con SIMEM o archivo
        if st.session_state["mostrar_grafica"]:
            data_fake = {
                "Tomate": [random.randint(0, 10) for _ in range(5)],
                "Cebolla": [random.randint(0, 10) for _ in range(5)],
            }
            st.line_chart(data_fake, height=300)

        # Registro simple de filtros aplicados
        st.markdown('<p style="font-weight:600;color:var(--accent);margin:0 0 var(--xs) 0;">Filtros aplicados</p>', unsafe_allow_html=True)
        st.write(st.session_state["filtros_aplicados"])

# =========================
# VISTA: Outliers
# =========================
# Placeholder de la sección de outliers
else:
    st.markdown('<div class="section-title">Outliers</div>', unsafe_allow_html=True)
    st.write("Outliers detectados: 0")
