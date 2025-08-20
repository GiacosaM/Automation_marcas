"""
Sistema de Gestión de Marcas - Estudio Contable
Aplicación principal refactorizada con arquitectura modular

Versión: 2.1.0
Autor: Sistema refactorizado
"""

import sys
import os
import json

# Configurar Streamlit ANTES de cualquier otra importación
import streamlit as st

# Configuración de página (debe ser lo primero)
st.set_page_config(
    page_title="Sistema de Gestión de Marcas",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Agregar el directorio src al path para importaciones
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime
import pandas as pd

# Importar módulos refactorizados
from src.config.settings import app_settings
from src.ui.styles import AppStyles
from src.ui.navigation import NavigationManager
from src.ui.components import UIComponents
from src.utils.session_manager import SessionManager

# Importar páginas
from src.ui.pages.dashboard import show_dashboard

# Importar módulos existentes (mantenemos la funcionalidad actual)
from auth_manager_simple import handle_authentication
from professional_theme import apply_professional_theme
from database import crear_conexion, limpieza_automatica_logs
from db_utils import convertir_query_boolean
from verificador_programado import inicializar_verificador_en_app, mostrar_panel_verificacion


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
        
        # Comentamos el tema profesional original para evitar conflictos CSS
        # apply_professional_theme()
    
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
                        hoy = datetime.now()
                        dia_del_mes = hoy.day
                        if dia_del_mes <= 7:  # Ejecutar solo la primera semana de cada mes
                            from verificar_titulares_sin_reportes import verificar_titulares_sin_reportes
                            resultado_verificacion = verificar_titulares_sin_reportes(conn)
                            SessionManager.set('resultado_verificacion_reportes', resultado_verificacion)
                        
                        SessionManager.set('sistema_inicializado', True)
                    except Exception as e:
                        SessionManager.set('resultado_limpieza_automatica', {'mensaje': f'Error en limpieza: {e}'})
                        SessionManager.set('sistema_inicializado', True)
                    finally:
                        conn.close()
            except:
                SessionManager.set('sistema_inicializado', True)
    
    def _handle_navigation(self):
        """Configurar navegación lateral y devolver la página seleccionada"""
        with st.sidebar:
            st.image("imagenes/Logo.png", width=100)
            st.title("Sistema de Gestión")
            
            # Grupos de páginas
            main_pages = {
                "📊 Dashboard": "dashboard",
                "📄 Informes": "informes",
                "👥 Clientes": "clientes",
                "📧 Emails": "emails"
            }
            
            admin_pages = {
                "⚙️ Configuración": "settings",
                "🗄️ Base de Datos": "supabase_config",
                "⚡ Optimización": "optimization"
            }
            
            # Mostrar navegación principal
            st.subheader("Navegación")
            
            for label, page in main_pages.items():
                if st.sidebar.button(label, key=f"nav_{page}", use_container_width=True):
                    SessionManager.set_current_page(page)
                    st.session_state["rerun"] = True
            
            # Mostrar páginas administrativas
            st.subheader("Administración")
            
            for label, page in admin_pages.items():
                if st.sidebar.button(label, key=f"nav_{page}", use_container_width=True):
                    SessionManager.set_current_page(page)
                    st.session_state["rerun"] = True
            
            # Botón de cerrar sesión
            st.sidebar.markdown("---")
            if st.sidebar.button("🔒 Cerrar sesión", key="logout"):
                SessionManager.logout()
                st.session_state["rerun"] = True
        
        # Devolver página actual
        return SessionManager.get_current_page()
    
    def _route_to_page(self):
        """Enruta a la página seleccionada"""
        current_page = SessionManager.get_current_page()
        
        # Verificar si se necesita un reinicio
        if st.session_state.get("rerun", False):
            st.session_state["rerun"] = False
            # En lugar de usar experimental_rerun, redibujamos la interfaz
            st.experimental_set_query_params()
        
        if current_page == 'dashboard':
            self._show_dashboard()
        elif current_page == 'informes':
            self._show_informes_page()
        elif current_page == 'clientes':
            self._show_clientes_page()
        elif current_page == 'emails':
            self._show_emails_page()
        elif current_page == 'settings':
            self._show_settings_page()
        elif current_page == 'supabase_config':
            self._show_supabase_config_page()
        elif current_page == 'optimization':
            self._show_optimization_page()
        else:
            self._show_dashboard()  # Página por defecto
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
        # Verificar si debemos usar la versión optimizada
        use_optimized = False
        try:
            import json
            if os.path.exists("config.json"):
                with open("config.json", "r") as f:
                    config = json.load(f)
                    use_optimized = config.get("use_optimized_pages", False)
        except Exception:
            pass
            
        if use_optimized:
            from src.ui.pages.clientes_optimized import show_clientes_optimized_page
            show_clientes_optimized_page()
        else:
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
    
    def _show_settings_page(self):
        """Mostrar la página de configuración"""
        from src.ui.pages.settings import show_settings_page
        show_settings_page()
    
    def _show_supabase_config_page(self):
        """Mostrar la página de configuración de Supabase"""
        from src.ui.pages.supabase_config import show_supabase_config_page
        show_supabase_config_page()
        
    def _show_optimization_page(self):
        """Mostrar la página de optimización de rendimiento"""
        from src.ui.pages.optimization import show_optimization_page
        show_optimization_page()
    
    def run(self):
        """Ejecutar la aplicación principal"""
        # Inicializar verificador programado (ejecuta verificaciones automáticas)
        inicializar_verificador_en_app()
        
        # Verificar autenticación
        if not handle_authentication():
            st.stop()
        
        # Manejar navegación
        selected_tab = self._handle_navigation()
        
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
