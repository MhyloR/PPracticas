# Principal.py
import os, sys
import streamlit as st

# ---- (Plan B anti-ModuleNotFoundError) Asegurar raíz en sys.path ----
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.styles import inject_css
from core.state import ensure_defaults
from Views import documentacion, graficos, outliers

class AppConfig:
    @staticmethod
    def set_page():
        st.set_page_config(
            page_title="Monitor de Variables SIMEM",
            page_icon="🟪",
            layout="wide",
            initial_sidebar_state="expanded",
        )

class SimemApp:
    def run(self):
        AppConfig.set_page()
        inject_css()
        ensure_defaults()

        # Header
        st.markdown('<div class="app-header">MONITOR DE VARIABLES SIMEM</div>', unsafe_allow_html=True)

        # Sidebar (router)
        with st.sidebar:
            st.title("Equipo Analítica")
            vista = st.radio("Menú", ["Documentación", "Generación de gráficos", "Outliers"])

        # Routing
        if vista == "Documentación":
            documentacion.render()
        elif vista == "Generación de gráficos":
            graficos.render()
        else:
            outliers.render()

if __name__ == "__main__":
    SimemApp().run()