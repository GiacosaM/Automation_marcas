"""
Estilos CSS centralizados para la aplicación
"""
import streamlit as st


class AppStyles:
    """Gestión de estilos CSS para la aplicación"""
    
    @staticmethod
    def get_main_styles() -> str:
        """Retorna los estilos CSS principales"""
        return """
        <style>
            .expirado-titular {
            color: #000000 !important;
            font-weight: bold;
            }
            /* Card de error: fuerza color negro en todo el contenido */
            .error-card, .error-card * {
                color: #000 !important;
            }
            /* Card de warning: fuerza color negro en todo el contenido */
            .warning-card, .warning-card * {
                color: #000 !important;
            }
            /* Card de instrucciones: fuerza color negro en todo el contenido */
            .instructions-card, .instructions-card * {
                color: #000 !important;
            }
            .instructions-card h4 {
                margin-bottom: 1rem;
                font-weight: 700;
            }
            .instructions-card ol {
                margin: 0;
                padding-left: 1.5rem;
                line-height: 1.8;
            }
            .instructions-tip {
                background: #e7f3ff;
                padding: 1rem;
                border-radius: 8px;
                margin-top: 1rem;
                border-left: 4px solid #667eea;
                color: #000 !important;
            }
            /* Reset y configuración base */
            .stApp {
                background-color: #0f0f0f;
                color: #e5e5e5;
                font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }
            
            .main {
                padding: 1rem 2rem;
                max-width: 1400px;
                margin: 0 auto;
                background-color: #0f0f0f;
            }
            
            /* Background para toda la aplicación */
            .stApp > div {
                background-color: #0f0f0f;
            }
            
            /* Contenedor principal más espacioso */
            .block-container {
                padding: 2rem 1rem;
                max-width: 1200px;
            }
            
            /* Header principal mejorado */
            .main-header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                margin-bottom: 2rem;
                color: white;
                text-align: center;
                box-shadow: 0 8px 32px rgba(102, 126, 234, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            .main-header h1 {
                font-size: 2.5rem;
                font-weight: 700;
                margin: 0;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .main-header p {
                font-size: 1.1rem;
                margin: 0.5rem 0 0 0;
                opacity: 0.9;
            }
            
            /* Cards de estadísticas - tema oscuro mejorado */
            .metric-card {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                border-left: 4px solid #667eea;
                border: 1px solid #333;
                margin: 1rem 0;
                transition: all 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.4);
            }
            
            /* Navegación mejorada */
            .stTabs [data-baseweb="tab-list"] {
                gap: 1rem;
                padding: 1rem 0;
                background-color: transparent;
            }
            
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                padding: 0 2rem;
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border-radius: 10px;
                border: 1px solid #333;
                color: #e5e5e5;
                transition: all 0.3s ease;
            }
            
            .stTabs [data-baseweb="tab"]:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                transform: translateY(-2px);
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
            }
            
            /* Botones mejorados */
            .stButton > button {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0.75rem 1.5rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                margin: 0.5rem 0;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }
            
            /* Espaciado general mejorado */
            .row-widget {
                margin: 1rem 0;
            }
            
            .stColumns {
                gap: 1rem;
            }
            
            .stExpander {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 10px;
                margin: 1rem 0;
            }
            
            .stExpander > div > div {
                background-color: #1a1a1a !important;
                color: #e5e5e5 !important;
            }
            
            .stExpander summary {
                background-color: #2d2d2d !important;
                color: #e5e5e5 !important;
                border-radius: 10px 10px 0 0;
            }
            
            .stExpander [data-testid="stExpander"] {
                background-color: #1a1a1a !important;
            }
            
            /* Text elements en expanders */
            .stExpander .stMarkdown {
                color: #e5e5e5 !important;
            }
            
            .stExpander p, .stExpander span, .stExpander div {
                color: #e5e5e5 !important;
            }
            
            /* Métricas mejoradas */
            [data-testid="metric-container"] {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border: 1px solid #333;
                padding: 1.5rem;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                margin: 0.5rem;
            }
            
            /* Sidebar oscuro */
            .css-1d391kg {
                background-color: #1a1a1a;
            }
            
            /* Elementos de texto */
            .stMarkdown {
                color: #e5e5e5;
            }
            
            /* Elementos st.text() */
            .stText {
                color: #e5e5e5 !important;
            }
            
            pre {
                background-color: #2d2d2d !important;
                color: #e5e5e5 !important;
                border: 1px solid #444;
                border-radius: 8px;
                padding: 1rem;
            }
            
            code {
                background-color: #2d2d2d;
                color: #e5e5e5;
                padding: 0.2rem 0.4rem;
                border-radius: 4px;
            }
            
            /* Inputs y selectbox */
            .stSelectbox > div > div {
                background-color: #2d2d2d;
                color: #e5e5e5;
                border: 1px solid #444;
            }
            
            .stTextInput > div > div > input {
                background-color: #2d2d2d;
                color: #e5e5e5;
                border: 1px solid #444;
            }
            
            .stFileUploader > div {
                background-color: #2d2d2d;
                border: 2px dashed #667eea;
                border-radius: 10px;
            }
            
            /* Headers y títulos */
            h1, h2, h3, h4, h5, h6 {
                color: #e5e5e5 !important;
            }
        </style>
        """
    
    @staticmethod
    def get_grid_styles() -> str:
        """Retorna los estilos específicos para ag-Grid"""
        return """
        <style>
            /* Estilos para ag-Grid - tema oscuro */
            .ag-theme-streamlit {
                --ag-background-color: #1a1a1a;
                --ag-foreground-color: #e5e5e5;
                --ag-header-background-color: #2d2d2d;
                --ag-header-foreground-color: #e5e5e5;
                --ag-header-cell-hover-background-color: #3d3d3d;
                --ag-row-hover-color: #2d2d2d;
                --ag-selected-row-background-color: rgba(102, 126, 234, 0.2);
                --ag-border-color: #444;
                --ag-font-family: inherit;
                --ag-font-size: 14px;
            }
            
            .ag-theme-streamlit .ag-header-cell {
                font-weight: 600;
                border-bottom: 1px solid #444;
            }
            
            .ag-theme-streamlit .ag-cell {
                padding: 8px;
                border-bottom: 1px solid #333;
            }
            
            .ag-theme-streamlit .ag-row {
                background-color: #1a1a1a;
            }
            
            .ag-theme-streamlit .ag-row:hover {
                background-color: #2d2d2d;
            }
        </style>
        """
    
    @staticmethod
    def get_email_styles() -> str:
        """Retorna los estilos específicos para la sección de emails"""
        return """
        <style>
            /* Forzar color negro en titulares de reportes vencidos */
            .expirado-titular, .stMarkdown .expirado-titular, .stExpander .expirado-titular {
                color: #000 !important;
                font-weight: 500 !important;
            }
            .vencimiento-chip, .stMarkdown .vencimiento-chip, .stExpander .vencimiento-chip {
                color: #000 !important;
                font-weight: 600 !important;
            }
            /* Estilos para la sección de emails - tema oscuro */
            .email-section {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                padding: 20px;
                border-radius: 10px;
                margin: 10px 0;
                border: 1px solid #444;
            }
            
            .email-config-card {
                background: #2d2d2d;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                margin: 10px 0;
                border: 1px solid #444;
                color: #e5e5e5;
            }
            
            /* Estilos para botones de gestión de emails */
            .email-management-container {
                background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%);
                padding: 20px;
                border-radius: 12px;
                margin: 15px 0;
                border: 1px solid #4a4a5a;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
            
            .email-management-title {
                color: #e5e5e5;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 20px;
                text-align: center;
                background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            /* Botones primarios de email con estilo avanzado */
            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0.6rem 1.2rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                text-transform: none;
                font-size: 0.95rem;
            }
            
            .stButton > button[kind="primary"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
                background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            }
        </style>
        """
    
    @staticmethod
    def get_tab_styles() -> str:
        """Retorna los estilos para las pestañas"""
        return """
        <style>
            /* Pestañas de email con colores específicos - Mayor especificidad */
            .email-management-container .stTabs [data-baseweb="tab-list"] {
                background: linear-gradient(135deg, #2d2d3d 0%, #3d3d4d 100%) !important;
                border-radius: 12px !important;
                padding: 6px !important;
                margin-bottom: 25px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
                border: 1px solid #4a4a5a !important;
            }
            
            .email-management-container .stTabs [data-baseweb="tab"] {
                background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3d 100%) !important;
                color: #b5b5c3 !important;
                border: 1px solid #3a3a4a !important;
                border-radius: 8px !important;
                margin: 0 3px !important;
                transition: all 0.3s ease !important;
                font-weight: 600 !important;
                padding: 12px 20px !important;
                font-size: 0.9rem !important;
                text-transform: none !important;
                min-height: 45px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            
            .email-management-container .stTabs [data-baseweb="tab"]:hover {
                background: linear-gradient(135deg, #3d3d4d 0%, #4d4d5d 100%) !important;
                color: #667eea !important;
                border-color: #667eea !important;
                transform: translateY(-2px) !important;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2) !important;
            }
            
            .email-management-container .stTabs [data-baseweb="tab"][aria-selected="true"] {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                color: white !important;
                border-color: #5a6fd8 !important;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4) !important;
                transform: translateY(-2px) !important;
                font-weight: 700 !important;
            }
        </style>
        """
    
    @staticmethod
    def apply_all_styles():
        """Aplicar todos los estilos CSS"""
        st.markdown(AppStyles.get_main_styles(), unsafe_allow_html=True)
        st.markdown(AppStyles.get_grid_styles(), unsafe_allow_html=True)
        st.markdown(AppStyles.get_email_styles(), unsafe_allow_html=True)
        st.markdown(AppStyles.get_tab_styles(), unsafe_allow_html=True)
