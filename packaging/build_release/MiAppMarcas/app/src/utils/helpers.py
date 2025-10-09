"""
Funciones de utilidad para la aplicación
"""
import streamlit as st
import pandas as pd
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import sys
import os

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from config import load_email_credentials, save_email_credentials, validate_email_format


class ValidationUtils:
    """Utilidades para validación de datos"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validar formato de email"""
        return validate_email_format(email)
    
    @staticmethod
    def validate_file_size(file_size: int, max_size_kb: int = 10240) -> bool:
        """Validar tamaño de archivo"""
        size_kb = file_size / 1024
        return size_kb <= max_size_kb
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """Validar extensión de archivo"""
        if not filename:
            return False
        extension = filename.split('.')[-1].lower()
        return extension in [ext.lower() for ext in allowed_extensions]


class DateUtils:
    """Utilidades para manejo de fechas"""
    
    @staticmethod
    def parse_date_string(date_str: str, format_str: str = "%d/%m/%Y") -> Optional[datetime]:
        """Parsear string de fecha"""
        try:
            return datetime.strptime(date_str, format_str)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def format_date(date_obj: datetime, format_str: str = "%d/%m/%Y") -> str:
        """Formatear fecha como string"""
        if not isinstance(date_obj, datetime):
            return ""
        return date_obj.strftime(format_str)
    
    @staticmethod
    def days_between(date1: datetime, date2: datetime) -> int:
        """Calcular días entre dos fechas"""
        if not isinstance(date1, datetime) or not isinstance(date2, datetime):
            return 0
        return (date2 - date1).days
    
    @staticmethod
    def is_date_expired(date_str: str, days_limit: int = 30) -> bool:
        """Verificar si una fecha ha expirado"""
        date_obj = DateUtils.parse_date_string(date_str)
        if not date_obj:
            return False
        
        expiry_date = date_obj + timedelta(days=days_limit)
        return datetime.now() > expiry_date


class DataUtils:
    """Utilidades para manejo de datos"""
    
    @staticmethod
    def safe_get(data: Dict, key: str, default: Any = None) -> Any:
        """Obtener valor de diccionario de forma segura"""
        return data.get(key, default) if isinstance(data, dict) else default
    
    @staticmethod
    def clean_string(text: str) -> str:
        """Limpiar string eliminando espacios extra"""
        if not isinstance(text, str):
            return ""
        return text.strip()
    
    @staticmethod
    def truncate_string(text: str, max_length: int = 50) -> str:
        """Truncar string a una longitud máxima"""
        if not isinstance(text, str):
            return ""
        return text[:max_length] + "..." if len(text) > max_length else text
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Formatear tamaño de archivo"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    @staticmethod
    def calculate_percentage(value: int, total: int) -> float:
        """Calcular porcentaje de forma segura"""
        if total == 0:
            return 0.0
        return (value / total) * 100


class UIUtils:
    """Utilidades para la interfaz de usuario"""
    
    @staticmethod
    def show_success_message(message: str, duration: int = 3) -> None:
        """Mostrar mensaje de éxito temporal"""
        success_placeholder = st.empty()
        success_placeholder.success(message)
        # En un caso real, aquí se usaría time.sleep() pero en Streamlit
        # es mejor usar st.rerun() cuando sea necesario
    
    @staticmethod
    def show_error_message(message: str) -> None:
        """Mostrar mensaje de error"""
        st.error(f"❌ {message}")
    
    @staticmethod
    def show_warning_message(message: str) -> None:
        """Mostrar mensaje de advertencia"""
        st.warning(f"⚠️ {message}")
    
    @staticmethod
    def show_info_message(message: str) -> None:
        """Mostrar mensaje informativo"""
        st.info(f"ℹ️ {message}")
    
    @staticmethod
    def create_download_button(data: bytes, filename: str, mime_type: str, 
                              label: str = "Descargar") -> None:
        """Crear botón de descarga"""
        st.download_button(
            label=label,
            data=data,
            file_name=filename,
            mime=mime_type
        )


class EmailUtils:
    """Utilidades para manejo de emails"""
    
    @staticmethod
    def load_credentials() -> Dict[str, Any]:
        """Cargar credenciales de email"""
        return load_email_credentials()
    
    @staticmethod
    def save_credentials(email: str, password: str) -> bool:
        """Guardar credenciales de email"""
        return save_email_credentials(email, password)
    
    @staticmethod
    def validate_credentials(email: str, password: str) -> tuple:
        """
        Validar credenciales de email
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not email or not password:
            return False, "Email y contraseña son requeridos"
        
        if not ValidationUtils.validate_email(email):
            return False, "Formato de email inválido"
        
        if len(password) < 8:
            return False, "La contraseña debe tener al menos 8 caracteres"
        
        return True, ""


class ReportUtils:
    """Utilidades para manejo de reportes"""
    
    @staticmethod
    def calculate_report_status(data: Dict) -> Dict[str, int]:
        """Calcular estado de reportes"""
        total = data.get('total_boletines', 0)
        generated = data.get('reportes_generados', 0)
        sent = data.get('reportes_enviados', 0)
        
        return {
            'pending_generation': total - generated,
            'pending_sending': generated - sent,
            'completed': sent,
            'generation_percentage': DataUtils.calculate_percentage(generated, total),
            'sending_percentage': DataUtils.calculate_percentage(sent, generated)
        }
    
    @staticmethod
    def get_urgency_level(days_remaining: int) -> str:
        """Obtener nivel de urgencia basado en días restantes"""
        if days_remaining <= 0:
            return "expired"
        elif days_remaining <= 3:
            return "critical"
        elif days_remaining <= 7:
            return "urgent"
        else:
            return "normal"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Obtener color basado en estado"""
        colors = {
            'expired': '#dc3545',
            'critical': '#dc3545', 
            'urgent': '#ffc107',
            'normal': '#28a745',
            'completed': '#17a2b8'
        }
        return colors.get(status, '#6c757d')
