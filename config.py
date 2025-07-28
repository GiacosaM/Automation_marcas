# config.py - Sistema de configuración centralizado

import os
import json
import logging
from pathlib import Path

class ConfigManager:
    """Gestor de configuración centralizado."""
    
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.default_config = {
            "app": {
                "title": "Sistema de Gestión de Marcas",
                "company_name": "Mi Estudio Contable",
                "logo_path": "imagenes/logo.png"
            },
            "database": {
                "name": "boletines.db",
                "backup_enabled": True,
                "backup_interval_hours": 24
            },
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "batch_size": 10,
                "retry_attempts": 3,
                "timeout_seconds": 30
            },
            "reports": {
                "output_dir": "informes",
                "watermark_path": "imagenes/marca_agua.jpg",
                "font_size": 10,
                "include_charts": True
            },
            "ui": {
                "items_per_page": 10,
                "theme": "professional",
                "show_advanced_filters": True
            },
            "logging": {
                "level": "INFO",
                "max_file_size_mb": 10,
                "backup_count": 5
            }
        }
        self.config = self.load_config()
    
    def load_config(self):
        """Carga la configuración desde archivo."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge con configuración por defecto
                config = self.default_config.copy()
                config.update(loaded_config)
                return config
            else:
                # Crear archivo de configuración por defecto
                self.save_config(self.default_config)
                return self.default_config.copy()
        
        except Exception as e:
            logging.error(f"Error cargando configuración: {e}")
            return self.default_config.copy()
    
    def save_config(self, config=None):
        """Guarda la configuración actual."""
        try:
            config_to_save = config or self.config
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=4, ensure_ascii=False)
            logging.info(f"Configuración guardada en {self.config_file}")
        except Exception as e:
            logging.error(f"Error guardando configuración: {e}")
    
    def get(self, key_path, default=None):
        """Obtiene un valor de configuración usando dot notation."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value):
        """Establece un valor de configuración usando dot notation."""
        keys = key_path.split('.')
        config_ref = self.config
        
        try:
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            config_ref[keys[-1]] = value
            self.save_config()
        except Exception as e:
            logging.error(f"Error estableciendo configuración {key_path}: {e}")

# Instancia global
config = ConfigManager()

# Funciones helper
def get_config(key_path, default=None):
    """Función helper para obtener configuración."""
    return config.get(key_path, default)

def set_config(key_path, value):
    """Función helper para establecer configuración."""
    config.set(key_path, value)

# settings_page.py - Página de configuración para Streamlit
import streamlit as st

def show_settings_page():
    """Página de configuración en Streamlit."""
    st.header("⚙️ Configuración del Sistema")
    
    # Configuración de la aplicación
    with st.expander("🏢 Configuración General", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            app_title = st.text_input(
                "Título de la Aplicación",
                value=get_config("app.title", "Sistema de Gestión de Marcas")
            )
            
            company_name = st.text_input(
                "Nombre de la Empresa",
                value=get_config("app.company_name", "Mi Estudio Contable")
            )
        
        with col2:
            logo_path = st.text_input(
                "Ruta del Logo",
                value=get_config("app.logo_path", "imagenes/logo.png")
            )
            
            items_per_page = st.number_input(
                "Elementos por Página",
                min_value=5,
                max_value=100,
                value=get_config("ui.items_per_page", 10)
            )
    
    # Configuración de email
    with st.expander("📧 Configuración de Email"):
        col1, col2 = st.columns(2)
        
        with col1:
            smtp_server = st.text_input(
                "Servidor SMTP",
                value=get_config("email.smtp_server", "smtp.gmail.com")
            )
            
            batch_size = st.number_input(
                "Tamaño de Lote",
                min_value=1,
                max_value=50,
                value=get_config("email.batch_size", 10)
            )
        
        with col2:
            smtp_port = st.number_input(
                "Puerto SMTP",
                min_value=1,
                max_value=65535,
                value=get_config("email.smtp_port", 587)
            )
            
            timeout_seconds = st.number_input(
                "Timeout (segundos)",
                min_value=10,
                max_value=300,
                value=get_config("email.timeout_seconds", 30)
            )
    
    # Configuración de reportes
    with st.expander("📄 Configuración de Reportes"):
        col1, col2 = st.columns(2)
        
        with col1:
            output_dir = st.text_input(
                "Directorio de Salida",
                value=get_config("reports.output_dir", "informes")
            )
            
            font_size = st.number_input(
                "Tamaño de Fuente",
                min_value=8,
                max_value=16,
                value=get_config("reports.font_size", 10)
            )
        
        with col2:
            watermark_path = st.text_input(
                "Ruta Marca de Agua",
                value=get_config("reports.watermark_path", "imagenes/marca_agua.jpg")
            )
            
            include_charts = st.checkbox(
                "Incluir Gráficos",
                value=get_config("reports.include_charts", True)
            )
    
    # Botón para guardar configuración
    if st.button("💾 Guardar Configuración", type="primary"):
        try:
            # Actualizar configuración
            set_config("app.title", app_title)
            set_config("app.company_name", company_name)
            set_config("app.logo_path", logo_path)
            set_config("ui.items_per_page", items_per_page)
            set_config("email.smtp_server", smtp_server)
            set_config("email.smtp_port", smtp_port)
            set_config("email.batch_size", batch_size)
            set_config("email.timeout_seconds", timeout_seconds)
            set_config("reports.output_dir", output_dir)
            set_config("reports.watermark_path", watermark_path)
            set_config("reports.font_size", font_size)
            set_config("reports.include_charts", include_charts)
            
            st.success("✅ Configuración guardada exitosamente")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error al guardar configuración: {e}")
    
    # Botón para restaurar valores por defecto
    if st.button("🔄 Restaurar Valores por Defecto"):
        config.config = config.default_config.copy()
        config.save_config()
        st.success("✅ Configuración restaurada a valores por defecto")
        st.rerun()