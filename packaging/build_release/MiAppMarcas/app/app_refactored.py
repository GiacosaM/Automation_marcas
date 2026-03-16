"""
Sistema de Gestión de Marcas - Estudio Contable
Aplicación principal refactorizada con arquitectura modular

Versión: 2.1.0
Autor: Sistema refactorizado
"""

import sys
import os
import json
import warnings

# Ocultar warnings de pandas sobre parsing de fechas
warnings.filterwarnings(
    "ignore",
    message="Parsing dates in %Y-%m-%dT%H:%M:%S format when dayfirst=True"
)

# Ocultar warning de conflicto PyFPDF / fpdf2
warnings.filterwarnings(
    "ignore",
    message="You have both PyFPDF & fpdf2 installed"
)

# Configurar Streamlit ANTES de cualquier otra importación
import streamlit as st

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Sistema de Gestión de Marca",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Agregar el directorio src al path para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
import pandas as pd

# Importar módulos refactorizados
# from src.config.settings import app_settings
from src.ui.styles import AppStyles
from src.ui.navigation import NavigationManager
from src.ui.components import UIComponents
from src.utils.session_manager import SessionManager

# Importar páginas
from src.ui.pages.dashboard import show_dashboard
from src.ui.pages.marcas import show_marcas_page
# La página email_config se importará dinámicamente para mejorar el rendimiento

# Importar módulos existentes (mantenemos la funcionalidad actual)
from auth_manager_simple import handle_authentication
from database import crear_conexion, limpieza_automatica_logs
#from verificador_programado import inicializar_verificador_en_app, mostrar_panel_verificacion

# Configuración centralizada de logging: consola solo WARNING/ERROR, archivo logs/app.log con INFO+
from logging_config import setup_logging
setup_logging()


class MarcasApp:
    """Aplicación principal del Sistema de Gestión de Marcas"""
    
    def __init__(self):
        """Inicializar la aplicación"""
        self._setup_app()
        self._initialize_system()
    
    def _setup_app(self):
        """Configurar la aplicación"""
        # Aplicar solo los estilos modulares (evitar conflictos)
        AppStyles.apply_all_styles()
    
    def _initialize_system(self):
        """Inicializar el sistema una sola vez por sesión"""
        if not SessionManager.get('sistema_inicializado', False):
            try:
                conn = crear_conexion()
                if conn:
                    try:
                        # Limpieza automática de logs
                        resultado_limpieza = limpieza_automatica_logs(conn)
                        SessionManager.set('resultado_limpieza_automatica', resultado_limpieza)
                        
                        # Verificar titulares sin reportes (primera semana del mes)
                        # DESACTIVADO: Para evitar ejecución automática al iniciar la app
                        # hoy = datetime.now()
                        # dia_del_mes = hoy.day
                        # if dia_del_mes <= 7:  # Ejecutar solo la primera semana de cada mes
                        #     from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes
                        #     resultado_verificacion = verificar_titulares_sin_reportes(conn)
                        #     SessionManager.set('resultado_verificacion_reportes', resultado_verificacion)
                        
                        SessionManager.set('sistema_inicializado', True)
                    except Exception as e:
                        SessionManager.set('resultado_limpieza_automatica', {'mensaje': f'Error en limpieza: {e}'})
                        SessionManager.set('sistema_inicializado', True)
                    finally:
                        conn.close()
            except:
                SessionManager.set('sistema_inicializado', True)
    
    def _handle_navigation(self):
        """Manejar la navegación de la aplicación"""
        # Crear menú de navegación
        selected_tab = NavigationManager.create_navigation_menu()
        
        # Manejar la navegación
        NavigationManager.handle_navigation(selected_tab)
        
        return selected_tab
    
    def _route_to_page(self):
        """Enrutar a la página correspondiente según el estado actual"""
        current_page = NavigationManager.get_current_page()
        
        # Debug para navegación
        if self._is_debug_mode():
            st.sidebar.write(f"Página actual: {current_page}")
            if current_page == 'config':
                st.sidebar.write(f"Sección config activa: {NavigationManager.is_section_active('config')}")
        
        if current_page == 'dashboard':
            self._show_dashboard()
        elif current_page == 'upload':
            self._show_upload_page()
        elif current_page == 'historial' and NavigationManager.is_section_active('db'):
            self._show_historial_page()
        elif current_page == 'clientes' and NavigationManager.is_section_active('clientes'):
            self._show_clientes_page()
        elif current_page == 'informes':
            self._show_informes_page()
        elif current_page == 'marcas' and NavigationManager.is_section_active('marcas'):
            self._show_marcas_page()
        elif current_page == 'emails' and NavigationManager.is_section_active('email'):
            self._show_emails_page()
        elif current_page == 'config':
            self._show_settings_page()
        else:
            # Por defecto mostrar dashboard
            self._show_dashboard()
    
    def _show_dashboard(self):
        """Mostrar la página de dashboard"""
        show_dashboard()
    
    def _show_upload_page(self):
        """Mostrar la página de carga de datos"""
        from src.ui.pages.upload import show_upload_page
        show_upload_page()
    
    def _show_historial_page(self):
        """Mostrar la página de historial"""
        from src.ui.pages.historial import show_historial_page
        show_historial_page()
    
    def _show_clientes_page(self):
        """Mostrar la página de clientes"""
        from src.ui.pages.clientes import show_clientes_page
        show_clientes_page()
    
    def _show_informes_page(self):
        """Mostrar la página de informes"""
        from src.ui.pages.informes import show_informes_page
        show_informes_page()
    
    def _show_emails_page(self):
        """Mostrar la página de emails"""
        from src.ui.pages.emails import show_emails_page
        show_emails_page()
    
    def _show_marcas_page(self):
        """Mostrar la página de marcas"""
        show_marcas_page()
    
    def _show_settings_page(self):
        """Mostrar la página de configuración"""
        # Mostrar secciones de configuración según la sección activa
        st.title("⚙️ Configuración del Sistema")
        
        # Crear tabs para distintas secciones
        tabs = st.tabs(["🔐 Email"])
        
        # Tab de configuración de email
        with tabs[0]:
            from src.ui.pages.email_config import show_email_config_page
            show_email_config_page()
            
        
    
    def run(self):
        """Ejecutar la aplicación principal"""
        # Inicializar verificador programado (ejecuta verificaciones automáticas)
        #inicializar_verificador_en_app()
        
        # Verificar autenticación
        if not handle_authentication():
            st.stop()
        
        # Manejar navegación
        selected_tab = self._handle_navigation()
        
        # Verificar si el usuario hizo clic en Configuración
        if selected_tab == "Configuración":
            # Configurar manualmente la página y la sección
            SessionManager.set_current_page('config', reset_sections=True)
            SessionManager.set('show_config_section', True)
        
        # Enrutar a la página correspondiente
        self._route_to_page()
        
        # Mostrar información de debug en desarrollo (opcional)
        if self._is_debug_mode():
            self._show_debug_info()
    
    def _is_debug_mode(self):
        """Verificar si está en modo debug"""
        # Verificar variable de entorno
        env_debug = os.getenv("DEBUG_MODE", "false").lower() == "true"
        
        # Verificar archivo de configuración local (opcional)
        try:
            if os.path.exists("config.json"):
                with open("config.json", 'r') as f:
                    config = json.load(f)
                    file_debug = config.get("debug_mode", False)
                    return env_debug or file_debug
        except:
            pass
        
        return env_debug
    
    def _show_debug_info(self):
        """Mostrar información de debug (solo en modo desarrollo)"""
        with st.expander("🔍 Debug Info", expanded=False):
            session_info = SessionManager.get_session_info()
            st.json(session_info)


def main():
    """Función principal de la aplicación"""
    try:
        app = MarcasApp()
        app.run()
    except Exception as e:
        st.error(f"Error fatal en la aplicación: {e}")
        st.stop()


if __name__ == "__main__":
    main()
