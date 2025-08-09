import streamlit as st

def apply_professional_theme():
    """Aplica el tema profesional para el estudio contable"""
    
    st.markdown("""
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
    
    /* Success alert */
    .stAlert[data-baseweb="notification"][kind="success"] {
        background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
        color: white;
    }
    
    /* Error alert */
    .stAlert[data-baseweb="notification"][kind="error"] {
        background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
        color: white;
    }
    
    /* Warning alert */
    .stAlert[data-baseweb="notification"][kind="warning"] {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
        color: white;
    }
    
    /* Info alert */
    .stAlert[data-baseweb="notification"][kind="info"] {
        background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%);
        color: white;
    }
    
    /* Mejorar el contraste del texto en alertas */
    .stAlert .stMarkdown {
        color: white !important;
    }
    
    .stAlert .stMarkdown p {
        color: white !important;
        margin: 0;
    }
    
    /* Animaciones */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in-up {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Contenedor principal */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
    }
    
    /* Títulos de sección */
    .section-title {
        color: #495057;
        font-size: 1.8rem;
        font-weight: 700;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #667eea;
        position: relative;
    }
    
    .section-title::after {
        content: '';
        position: absolute;
        bottom: -3px;
        left: 0;
        width: 50px;
        height: 3px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    /* Footer */
    .footer {
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 16px;
        margin-top: 3rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        color: white;
        margin: 0.2rem;
    }
    
    .status-activo {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
    }
    
    .status-vencido {
        background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
    }
    
    .status-proximo {
        background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
    }
    
    /* Loading spinner personalizado */
    .custom-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-radius: 50%;
        border-top-color: #667eea;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header {
            padding: 1rem;
        }
        
        .main-header h1 {
            font-size: 2rem;
        }
        
        .professional-card {
            padding: 1rem;
        }
        
        .main-container {
            padding: 1rem;
        }
    }
    
    /* Ocultar elementos de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Hacer el sidebar más elegante */
    .css-1d391kg {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Personalizar el option menu */
    .nav-link-wrapper {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    
    .nav-link-wrapper:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateX(5px);
    }
    </style>
    """, unsafe_allow_html=True)

def create_professional_card(title, content, icon=None):
    """Crea una tarjeta profesional con contenido"""
    icon_html = f'<i class="{icon}" style="margin-right: 10px; color: #667eea;"></i>' if icon else ''
    
    return f"""
    <div class="professional-card fade-in-up">
        <h3 style="color: #495057; margin: 0 0 1rem 0; font-weight: 600;">
            {icon_html}{title}
        </h3>
        <div style="color: #6c757d;">
            {content}
        </div>
    </div>
    """

def create_metric_card(value, label, color="#667eea"):
    """Crea una tarjeta de métrica profesional"""
    return f"""
    <div class="metric-card fade-in-up">
        <div class="metric-value" style="color: {color};">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """

def create_status_badge(status, text):
    """Crea un badge de estado"""
    return f'<span class="status-badge status-{status}">{text}</span>'

def show_loading_spinner():
    """Muestra un spinner de carga personalizado"""
    return '<div class="custom-spinner"></div>'
