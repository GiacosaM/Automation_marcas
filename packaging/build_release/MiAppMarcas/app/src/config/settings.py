"""
Configuración central de la aplicación
"""
import streamlit as st
from typing import Dict, Any
import os
import sys

# Agregar el directorio raíz al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import get_config, set_config, load_email_credentials, save_email_credentials
# Removemos la importación de PAGE_CONFIG ya que no se usa más aquí


class AppSettings:
    """Gestión centralizada de configuración de la aplicación"""
    
    def __init__(self):
        # Removemos la configuración de página ya que se hace en app_refactored.py
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Inicializar el estado de la sesión"""
        default_states = {
            'current_page': 'dashboard',
            'show_db_section': False,
            'show_clientes_section': False,
            'show_email_section': False,
            'selected_record_id': None,
            'selected_cliente_id': None,
            'db_data': None,
            'clientes_data': None,
            'pending_action': None,
            'pending_data': None,
            'datos_insertados': False,
            'email_credentials': self.load_email_credentials(),
            'confirmar_generar_informes': False,
            'email_config': self.load_email_credentials(),
            'confirmar_envio_emails': False,
            'resultados_envio': None,
            'sistema_inicializado': False,
            'cambios_procesados': set()
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def load_email_credentials() -> Dict[str, Any]:
        """Cargar credenciales de email"""
        return load_email_credentials()
    
    @staticmethod
    def save_email_credentials(email: str, password: str) -> bool:
        """Guardar credenciales de email"""
        return save_email_credentials(email, password)
    
    @staticmethod
    def get_email_credentials() -> Dict[str, Any]:
        """Obtener credenciales de email desde session_state o archivo"""
        if 'email_credentials' not in st.session_state:
            st.session_state.email_credentials = AppSettings.load_email_credentials()
        return st.session_state.email_credentials
    
    @staticmethod
    def update_page(page_name: str):
        """Actualizar la página actual y resetear secciones"""
        st.session_state.current_page = page_name
        st.session_state.show_db_section = False
        st.session_state.show_clientes_section = False
        st.session_state.show_email_section = False
    
    @staticmethod
    def activate_section(section_name: str):
        """Activar una sección específica"""
        sections = {
            'db': 'show_db_section',
            'clientes': 'show_clientes_section',
            'email': 'show_email_section'
        }
        
        # Resetear todas las secciones
        for section in sections.values():
            st.session_state[section] = False
        
        # Activar la sección solicitada
        if section_name in sections:
            st.session_state[sections[section_name]] = True


# Instancia global de configuración
app_settings = AppSettings()
