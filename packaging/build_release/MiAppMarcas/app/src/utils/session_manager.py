"""
Gestor de estado de sesión de Streamlit
"""
import streamlit as st
from typing import Any, Dict, Set
import time


class SessionManager:
    """Gestión centralizada del estado de la sesión"""
    
    @staticmethod
    def initialize_if_not_exists(key: str, default_value: Any) -> None:
        """Inicializar un valor en session_state si no existe"""
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Obtener un valor del session_state"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """Establecer un valor en session_state"""
        st.session_state[key] = value
    
    @staticmethod
    def delete(key: str) -> None:
        """Eliminar un valor del session_state"""
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def clear_all() -> None:
        """Limpiar todo el session_state"""
        st.session_state.clear()
    
    @staticmethod
    def add_to_set(key: str, value: Any) -> None:
        """Agregar un valor a un conjunto en session_state"""
        if key not in st.session_state:
            st.session_state[key] = set()
        st.session_state[key].add(value)
    
    @staticmethod
    def remove_from_set(key: str, value: Any) -> None:
        """Remover un valor de un conjunto en session_state"""
        if key in st.session_state and isinstance(st.session_state[key], set):
            st.session_state[key].discard(value)
    
    @staticmethod
    def is_in_set(key: str, value: Any) -> bool:
        """Verificar si un valor está en un conjunto"""
        return (key in st.session_state and 
                isinstance(st.session_state[key], set) and 
                value in st.session_state[key])
    
    @staticmethod
    def update_multiple(updates: Dict[str, Any]) -> None:
        """Actualizar múltiples valores en session_state"""
        for key, value in updates.items():
            st.session_state[key] = value
    
    @staticmethod
    def reset_navigation_sections() -> None:
        """Resetear todas las secciones de navegación"""
        sections_to_reset = [
            'show_db_section',
            'show_clientes_section', 
            'show_email_section',
            'show_config_section'
        ]
        for section in sections_to_reset:
            st.session_state[section] = False
    
    @staticmethod
    def set_current_page(page: str, reset_sections: bool = True) -> None:
        """Establecer la página actual y opcionalmente resetear secciones"""
        st.session_state.current_page = page
        print(f"Estableciendo página actual: {page}")
        if reset_sections:
            SessionManager.reset_navigation_sections()
    
    @staticmethod
    def track_change(change_id: str) -> bool:
        """
        Rastrear un cambio para evitar procesamiento múltiple
        Retorna True si el cambio ya fue procesado
        """
        if 'cambios_procesados' not in st.session_state:
            st.session_state.cambios_procesados = set()
        
        if change_id in st.session_state.cambios_procesados:
            return True
        
        st.session_state.cambios_procesados.add(change_id)
        return False
    
    @staticmethod
    def untrack_change(change_id: str) -> None:
        """Dejar de rastrear un cambio (útil para errores)"""
        if 'cambios_procesados' in st.session_state:
            st.session_state.cambios_procesados.discard(change_id)
    
    @staticmethod
    def get_session_info() -> Dict[str, Any]:
        """Obtener información sobre el estado actual de la sesión"""
        return {
            'keys_count': len(st.session_state.keys()),
            'current_page': st.session_state.get('current_page', 'unknown'),
            'user_role': st.session_state.get('user_info', {}).get('role', 'unknown'),
            'active_sections': [
                key for key in ['show_db_section', 'show_clientes_section', 'show_email_section', 'show_config_section']
                if st.session_state.get(key, False)
            ],
            'changes_tracked': len(st.session_state.get('cambios_procesados', set()))
        }
