"""
Sistema de navegación de la aplicación
"""
import streamlit as st
from streamlit_option_menu import option_menu
from typing import Optional
from src.config.constants import NAVIGATION_TABS
from src.utils.session_manager import SessionManager


class NavigationManager:
    """Gestor de navegación de la aplicación"""
    
    @staticmethod
    def create_navigation_menu() -> str:
        """
        Crear el menú de navegación principal
        
        Returns:
            Nombre de la pestaña seleccionada
        """
        # Extraer nombres e iconos de las pestañas
        tab_names = [tab["name"] for tab in NAVIGATION_TABS]
        tab_icons = [tab["icon"] for tab in NAVIGATION_TABS]
        
        # Crear el menú de navegación
        selected_tab = option_menu(
            menu_title=None,
            options=tab_names,
            icons=tab_icons,
            menu_icon="cast",
            default_index=0,
            orientation="horizontal",
            styles=NavigationManager._get_navigation_styles()
        )
        
        return selected_tab
    
    @staticmethod
    def _get_navigation_styles() -> dict:
        """Obtener estilos para el menú de navegación"""
        return {
            "container": {
                "padding": "1rem!important",
                "background": "linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)",
                "border": "1px solid #333",
                "border-radius": "15px",
                "margin-bottom": "2rem",
                "box-shadow": "0 8px 32px rgba(0, 0, 0, 0.3)",
                "backdrop-filter": "blur(10px)"
            },
            "icon": {
                "color": "#667eea", 
                "font-size": "20px",
                "margin-right": "8px"
            },
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "8px 4px",
                "padding": "12px 20px",
                "background-color": "rgba(45, 45, 45, 0.6)",
                "color": "#e5e5e5",
                "border-radius": "12px",
                "font-weight": "600",
                "transition": "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                "white-space": "nowrap",
                "position": "relative",
                "overflow": "hidden",
                "border": "1px solid #444"
            },
            "nav-link-selected": {
                "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "color": "white",
                "font-weight": "700",
                "box-shadow": "0 8px 25px rgba(102, 126, 234, 0.4)",
                "transform": "translateY(-2px)",
                "border": "1px solid rgba(102, 126, 234, 0.5)"
            }
        }
    
    @staticmethod
    def handle_navigation(selected_tab: str) -> None:
        """
        Manejar la navegación basada en la pestaña seleccionada
        
        Args:
            selected_tab: Nombre de la pestaña seleccionada
        """
        navigation_map = {
            'Dashboard': ('dashboard', {}),
            'Cargar Datos': ('upload', {}),
            'Historial': ('historial', {'show_db_section': True}),
            'Clientes': ('clientes', {'show_clientes_section': True}),
            'Marcas': ('marcas', {'show_marcas_section': True}),
            'Informes': ('informes', {}),
            'Emails': ('emails', {'show_email_section': True}),
            'Configuración': ('settings', {})
        }
        
        if selected_tab in navigation_map:
            page, sections = navigation_map[selected_tab]
            
            # Actualizar página actual
            SessionManager.set_current_page(page, reset_sections=True)
            
            # Activar secciones específicas
            for section_key, section_value in sections.items():
                SessionManager.set(section_key, section_value)
    
    @staticmethod
    def get_current_page() -> str:
        """Obtener la página actual"""
        return SessionManager.get('current_page', 'dashboard')
    
    @staticmethod
    def is_section_active(section_name: str) -> bool:
        """
        Verificar si una sección está activa
        
        Args:
            section_name: Nombre de la sección (db, clientes, email)
            
        Returns:
            True si la sección está activa
        """
        section_map = {
            'db': 'show_db_section',
            'clientes': 'show_clientes_section',
            'marcas': 'show_marcas_section',
            'email': 'show_email_section'
        }
        
        if section_name in section_map:
            return SessionManager.get(section_map[section_name], False)
        
        return False
    
    @staticmethod
    def activate_section(section_name: str) -> None:
        """
        Activar una sección específica
        
        Args:
            section_name: Nombre de la sección (db, clientes, email)
        """
        section_map = {
            'db': 'show_db_section',
            'clientes': 'show_clientes_section',
            'marcas': 'show_marcas_section',
            'email': 'show_email_section'
        }
        
        # Resetear todas las secciones
        SessionManager.reset_navigation_sections()
        
        # Activar la sección solicitada
        if section_name in section_map:
            SessionManager.set(section_map[section_name], True)
