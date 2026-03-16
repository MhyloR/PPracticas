import streamlit as st

# =========================
# Configuración
# =========================
st.set_page_config(page_title="Filtro (un solo punto visible)", page_icon="🟪", layout="centered")

ACCENT   = "#7C16E3"   # borde morado
PANEL_BG = "#2B3965"   # fondo del recuadro
TEXT     = "#E7E9EE"
MUTED    = "#9AA0AA"
RADIUS   = "12px"

# =========================
# Estilos
# =========================
st.markdown(f"""
<style>
  .st-key-filtro {{
    border: 2px solid {ACCENT};
    border-radius: {RADIUS};
    background: {PANEL_BG};
    padding: 16px 18px 18px;
    box-sizing: border-box;
  }}

  /* Título sin ancla */
  .st-key-filtro h3 {{
    margin: 0 0 12px;
    font-weight: 800;
    color: {TEXT};
    letter-spacing: .2px;
  }}
  .st-key-filtro h1 a, .st-key-filtro h2 a, .st-key-filtro h3 a {{ display: none !important; }}

  /* Reset por si el radio viene en <ul><li> */
  .st-key-filtro .stRadio ul {{ list-style: none; margin: 0; padding-left: 0; }}
  .st-key-filtro .stRadio li::marker {{ content: ''; }}

  /* Fila de opción: [punto][texto] */
  .st-key-filtro .stRadio div[role="radiogroup"] > label {{
    display: grid;
    grid-template-columns: 18px 1fr;
    align-items: center;
    column-gap: 10px;
    padding: 6px 4px;
    border-radius: 8px;
    line-height: 1.25;
    color: {TEXT};
  }}
  .st-key-filtro .stRadio div[role="radiogroup"] > label:hover {{
    background: rgba(255,255,255,0.06);
  }}

  /* Texto secundario */
  .st-key-filtro .muted {{ color: {MUTED}; font-size: .9rem; }}
</style>
""", unsafe_allow_html=True)

# =========================
# Estado
# =========================
if "filtro_sel" not in st.session_state:
    st.session_state.filtro_sel = "Etapa"

# =========================
# UI
# =========================
with st.container(border=True, key="filtro"):
    st.markdown("### Filtro")

    seleccion = st.radio(
        label="Selecciona un filtro",
        options=["Etapa", "Código Agente", "Actividad", "Código SIC Agente", "Versión"],
        index=["Etapa", "Código Agente", "Actividad", "Código SIC Agente", "Versión"].index(st.session_state.filtro_sel),
        label_visibility="collapsed",
        horizontal=False,
        key="filtro_radio",
    )

    st.session_state.filtro_sel = seleccion
    st.markdown(f"<div class='muted'>Opción actual: {st.session_state.filtro_sel}</div>", unsafe_allow_html=True)
