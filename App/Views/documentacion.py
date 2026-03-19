# views/documentacion.py
import streamlit as st

def render():
    st.markdown('<h2 style="color:#000;margin:0 0 var(--s) 0;">hola</h2>', unsafe_allow_html=True)
    st.markdown("""
      <div class="card">
        <h3>Heading</h3>
        <p>Aqui va a ir una cantidad de texto pero es que es mucha dejeme decirle</p>
      </div>
    """, unsafe_allow_html=True)