"""
Componentes reutilizables de la interfaz de usuario
"""
import streamlit as st
from streamlit_extras.grid import grid
from streamlit_extras.colored_header import colored_header
from typing import Dict, Any, List, Optional, Tuple


# Consolidated styles from professional_theme.py
st.markdown(
    """
    <style>
    /* Reset de estilos básicos */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Header profesional */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2rem 1rem 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }

    /* Cards profesionales */
    .professional-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .professional-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
    }

    .professional-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        border-radius: 16px 16px 0 0;
    }

    /* Botones mejorados */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Métricas mejoradas */
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #667eea;
        margin: 0;
    }

    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        font-weight: 500;
        margin: 0.5rem 0 0 0;
    }

    /* Sidebar profesional */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }

    .css-1d391kg .css-1aumxhk {
        color: white;
    }

    /* Navegación mejorada */
    .nav-link {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
        color: #495057;
        text-decoration: none;
        display: flex;
        align-items: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    .nav-link:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateX(5px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    .nav-link.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }

    /* Inputs profesionales */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input {
        border-radius: 12px;
        border: 2px solid #e9ecef;
        padding: 0.75rem 1rem;
        transition: all 0.3s ease;
        background: rgba(255, 255, 255, 0.95);
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
    }

    /* Dataframe mejorado */
    .stDataFrame {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Alertas profesionales */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        margin: 1rem 0;
    }

    .stAlert > div {
        padding: 1rem 1.5rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)


class UIComponents:
    """Componentes reutilizables de UI"""
    
    @staticmethod
    def create_metric_card(value: Any, label: str, color: str = "#667eea") -> str:
        """
        Crear una tarjeta de métrica HTML mejorada con efectos visuales
        
        Args:
            value: Valor a mostrar
            label: Etiqueta de la métrica
            color: Color del borde izquierdo
            
        Returns:
            HTML de la tarjeta
        """
        return f"""
        <div class="metric-card" style="
            border-left: 6px solid {color};
        ">
            <h2 style="color: {color}; margin: 0; font-size: 2rem;">{value}</h2>
            <p style="color: #e5e5e5; margin: 0.5rem 0 0 0; font-weight: 600;">{label}</p>
        </div>
        """
    
    @staticmethod
    def create_status_badge(status: str, days: int) -> str:
        """
        Crear un badge de estado
        
        Args:
            status: Estado ('vencido', 'proximo', 'activo')
            days: Número de días
            
        Returns:
            HTML del badge
        """
        colors = {
            'vencido': "#dc3545",
            'proximo': "#ffc107", 
            'activo': "#28a745"
        }
        
        icons = {
            'vencido': "🚨",
            'proximo': "⚠️",
            'activo': "✅"
        }
        
        color = colors.get(status, "#28a745")
        icon = icons.get(status, "✅")
        text_color = "#000" if status == 'proximo' else "white"
        
        return f"""
        <span style="
            background: {color}; 
            color: {text_color}; 
            padding: 4px 8px; 
            border-radius: 12px; 
            font-size: 0.75em; 
            font-weight: 600;
        ">
            {icon} {days} días {'restantes' if status != 'vencido' else 'vencido'}
        </span>
        """
    
    @staticmethod
    def create_info_card(title: str, content: str, card_type: str = "info") -> str:
        """
        Crear una tarjeta informativa
        
        Args:
            title: Título de la tarjeta
            content: Contenido de la tarjeta
            card_type: Tipo de tarjeta ('info', 'success', 'warning', 'error')
            
        Returns:
            HTML de la tarjeta
        """
        colors = {
            'info': {"bg": "#d1ecf1", "border": "#17a2b8", "icon": "ℹ️"},
            'success': {"bg": "#d4edda", "border": "#28a745", "icon": "✅"},
            'warning': {"bg": "#fff3cd", "border": "#ffc107", "icon": "⚠️"},
            'error': {"bg": "#f8d7da", "border": "#dc3545", "icon": "🚨"}
        }
        
        style_config = colors.get(card_type, colors['info'])
        
        return f"""
        <div style="
            background: {style_config['bg']}; 
            padding: 1rem; 
            border-radius: 8px; 
            border-left: 4px solid {style_config['border']}; 
            margin-top: 0.5rem; 
            color: #000000;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{style_config['icon']}</span>
                <h3 style="color: #000000 !important; margin: 0;">{title}</h3>
            </div>
            <div style="color: #000000;">{content}</div>
        </div>
        """
    
    @staticmethod
    def create_file_upload_area() -> str:
        """
        Crear área de carga de archivos estilizada
        
        Returns:
            HTML del área de carga
        """
        return """
        <div style="
            border: 2px dashed #667eea; 
            border-radius: 16px; 
            padding: 2rem; 
            text-align: center; 
            background: rgba(102, 126, 234, 0.05); 
            margin: 1rem 0;
        ">
            <div style="font-size: 3rem; color: #667eea; margin-bottom: 1rem;">📁</div>
            <h3 style="color: #495057; margin-bottom: 0.5rem;">Cargar Archivo XLSX</h3>
            <p style="color: #6c757d; margin-bottom: 1rem;">Arrastra tu archivo aquí o haz clic para seleccionar</p>
        </div>
        """
    
    @staticmethod
    def create_section_header(title: str, description: str, color: str = "blue-70") -> None:
        """
        Crear encabezado de sección usando colored_header
        
        Args:
            title: Título de la sección
            description: Descripción de la sección
            color: Color del encabezado
        """
        colored_header(
            label=title,
            description=description,
            color_name=color
        )
    
    @staticmethod
    def create_metric_grid(metrics: List[Dict[str, Any]], columns: int = 5) -> None:
        """
        Crear un grid de métricas
        
        Args:
            metrics: Lista de métricas con 'value', 'label' y 'color'
            columns: Número de columnas en el grid
        """
        metric_grid = grid(columns, vertical_align="center")
        
        for metric in metrics:
            with metric_grid.container():
                st.markdown(
                    UIComponents.create_metric_card(
                        metric['value'],
                        metric['label'],
                        metric.get('color', '#667eea')
                    ), 
                    unsafe_allow_html=True
                )
    
    @staticmethod
    def create_alert_grid(alerts: List[Dict[str, Any]], columns: int = 2) -> None:
        """
        Crear un grid de alertas
        
        Args:
            alerts: Lista de alertas con 'type', 'message' y 'details'
            columns: Número de columnas en el grid
        """
        alert_grid = grid(columns, vertical_align="top")
        
        for alert in alerts:
            with alert_grid.container():
                if alert['type'] == 'error':
                    st.error(alert['message'])
                elif alert['type'] == 'warning':
                    st.warning(alert['message'])
                elif alert['type'] == 'success':
                    st.success(alert['message'])
                else:
                    st.info(alert['message'])
                
                if 'details' in alert:
                    st.markdown(alert['details'], unsafe_allow_html=True)
    
    @staticmethod
    def create_file_info_card(filename: str, size_kb: float, file_type: str) -> str:
        """
        Crear tarjeta con información del archivo cargado
        
        Args:
            filename: Nombre del archivo
            size_kb: Tamaño en KB
            file_type: Tipo de archivo
            
        Returns:
            HTML de la tarjeta
        """
        return f"""
        <div style="
            background: #f8f9fa; 
            padding: 1.5rem; 
            border-radius: 12px; 
            box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
            margin: 1rem 0; 
            border-left: 4px solid #28a745;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="color: #28a745; font-size: 1.2rem; margin-right: 0.5rem;">📄</span>
                <h3 style="color: #000000 !important; margin: 0;">Archivo Cargado Exitosamente</h3>
            </div>
            <div style="margin: 1rem 0; color: #000000;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div style="color: #000000;">
                        <strong style="color: #000000;">Nombre:</strong> {filename}<br>
                        <strong style="color: #000000;">Tamaño:</strong> {size_kb} KB
                    </div>
                    <div style="color: #000000;">
                        <strong style="color: #000000;">Tipo:</strong> {file_type}<br>
                        <strong style="color: #000000;">Estado:</strong> 
                        <span style="
                            background: #28a745; 
                            color: white; 
                            padding: 4px 8px; 
                            border-radius: 12px; 
                            font-size: 0.75em; 
                            font-weight: 600;
                        ">✓ Válido</span>
                    </div>
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def create_data_preview_card(titular: str, registro_count: int, sample_record: dict) -> str:
        """
        Crear tarjeta de vista previa para un titular y sus datos
        
        Args:
            titular: Nombre del titular
            registro_count: Número de registros del titular
            sample_record: Registro de muestra
            
        Returns:
            HTML de la tarjeta de vista previa
        """
        # Extraer datos del registro con valores por defecto
        boletin = sample_record.get('Número de Boletín', 'N/A')
        marca = sample_record.get('Marca en Custodia', 'N/A')
        clase = sample_record.get('Clase', 'N/A')
        
        # Truncar marca si es muy larga
        marca_display = marca[:40] + '...' if len(str(marca)) > 40 else marca
        
        html = f'''
<div style="background: linear-gradient(135deg, #2d2d2d 0%, #1a1a1a 100%); padding: 1.5rem; border-radius: 12px; margin: 1rem 0; border-left: 4px solid #667eea; color: #e5e5e5; box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
    <div style="margin-bottom: 1rem;">
        <h4 style="color: #e5e5e5 !important; margin: 0 0 0.5rem 0; display: flex; align-items: center;">
            <span style="margin-right: 0.5rem;">👤</span>
            {titular}
        </h4>
        <span style="background: #667eea; color: white; padding: 6px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 600;">
            {registro_count} registros
        </span>
    </div>
    
    <div style="background: #1a1a1a; padding: 1.2rem; border-radius: 8px; border: 1px solid #333; margin-top: 1rem;">
        <p style="color: #888; margin: 0 0 1rem 0; font-size: 0.9em;">Ejemplo de registro:</p>
        <div style="display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 1.5rem;">
            <div style="border-right: 1px solid #333; padding-right: 1rem;">
                <strong style="color: #667eea; display: block; margin-bottom: 0.5rem;">📋 Boletín</strong>
                <span style="color: #e5e5e5; font-size: 0.95em;">{boletin}</span>
            </div>
            <div style="border-right: 1px solid #333; padding-right: 1rem;">
                <strong style="color: #28a745; display: block; margin-bottom: 0.5rem;">🏷️ Marca</strong>
                <span style="color: #e5e5e5; font-size: 0.95em;" title="{marca}">
                    {marca_display}
                </span>
            </div>
            <div>
                <strong style="color: #17a2b8; display: block; margin-bottom: 0.5rem;">🔢 Clase</strong>
                <span style="color: #e5e5e5; font-size: 0.95em;">{clase}</span>
            </div>
        </div>
    </div>
</div>
'''
        return html
    
    @staticmethod
    def show_loading_spinner(message: str = "Procesando...") -> None:
        """
        Mostrar spinner de carga
        
        Args:
            message: Mensaje a mostrar durante la carga
        """
        with st.spinner(f"🔄 {message}"):
            pass
