"""
Script para ejecutar directamente la página de configuración
"""

import streamlit as st
from src.ui.pages.db_config import show_db_config_page

if __name__ == "__main__":
    # Configurar página
    st.set_page_config(
        page_title="Configuración de Base de Datos",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Mostrar la página de configuración
    show_db_config_page()