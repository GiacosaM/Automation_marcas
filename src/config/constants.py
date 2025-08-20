"""
Constantes del sistema
"""

# Configuración de página
PAGE_CONFIG = {
    "page_title": "Sistema de Gestión de Marcas - Estudio Contable",
    "page_icon": "🏢",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

# Configuración de grid
GRID_CONFIG = {
    "pagination_page_size": 10,
    "clients_pagination_page_size": 20,
    "min_column_width": 100,
    "grid_height": 400,
    "clients_grid_height": 600
}

# Pestañas de navegación
NAVIGATION_TABS = [
    {"name": "Dashboard", "icon": "house"},
    {"name": "Cargar Datos", "icon": "upload"},
    {"name": "Historial", "icon": "clock-history"},
    {"name": "Clientes", "icon": "people"},
    {"name": "Informes", "icon": "file-earmark-text"},
    {"name": "Emails", "icon": "envelope"},
    {"name": "Configuración", "icon": "gear"},
    {"name": "Supabase", "icon": "database"}  # Nueva pestaña para Supabase
]

# Columnas del grid de boletines
BULLETIN_COLUMNS = {
    'numero_boletin': {"width": 120, "header_name": "N° Boletín"},
    'fecha_boletin': {"width": 120, "header_name": "Fecha"},
    'numero_orden': {"width": 120, "header_name": "N° Orden"},
    'solicitante': {"width": 200},
    'agente': {"width": 200},
    'numero_expediente': {"width": 150, "header_name": "N° Expediente"},
    'clase': {"width": 100},
    'marca_custodia': {"width": 200, "header_name": "Marca Custodia"},
    'marca_publicada': {"width": 200, "header_name": "Marca Publicada"},
    'clases_acta': {"width": 120, "header_name": "Clases"},
    'titular': {"width": 300, "wrapText": True, "autoHeight": True},
    'reporte_enviado': {
        "width": 120, 
        "header_name": "📤 Enviado",
        "cellStyle": {
            'textAlign': 'center',
            'backgroundColor': 'rgba(248,249,250,0.8)',
            'fontSize': '14px',
            'color': '#6c757d'
        }
    },
    'reporte_generado': {
        "width": 120, 
        "header_name": "📄 Generado",
        "cellStyle": {
            'textAlign': 'center',
            'backgroundColor': 'rgba(248,249,250,0.8)',
            'fontSize': '14px',
            'color': '#6c757d'
        }
    },
    'importancia': {
        "width": 120,
        "header_name": "⚡ Importancia",
        "editable": True,
        "cellEditor": 'agSelectCellEditor',
        "cellEditorParams": {'values': ['Baja', 'Media', 'Alta', 'Pendiente']},
        "cellStyle": {
            'cursor': 'pointer',
            'backgroundColor': 'rgba(255,255,255,0.1)',
            'textAlign': 'center'
        }
    }
}

# Columnas del grid de clientes
CLIENT_COLUMNS = {
    'id': {"hide": True},
    'titular': {"width": 200, "header_name": "👤 Titular", "pinned": 'left', "flex": 2},
    'email': {"width": 180, "header_name": "📧 Email", "flex": 2},
    'telefono': {"width": 130, "header_name": "📞 Teléfono", "flex": 1},
    'direccion': {"width": 250, "header_name": "📍 Dirección", "wrapText": True, "flex": 3},
    'ciudad': {"width": 120, "header_name": "🏙️ Ciudad", "flex": 1},
    'provincia': {"width": 130, "header_name": "🗺️ Provincia", "flex": 1},
    'cuit': {"width": 130, "header_name": "🆔 CUIT", "flex": 1}
}

# Opciones de importancia
IMPORTANCE_OPTIONS = ['Baja', 'Media', 'Alta', 'Pendiente']

# Navegación
NAVIGATION_TABS = [
    {"name": "Dashboard", "icon": "house-fill"},
    {"name": "Cargar Datos", "icon": "cloud-upload-fill"},
    {"name": "Historial", "icon": "list-task"},
    {"name": "Clientes", "icon": "people-fill"},
    {"name": "Informes", "icon": "file-earmark-text-fill"},
    {"name": "Emails", "icon": "envelope-fill"},
    {"name": "Configuración", "icon": "gear-fill"}
]

# Colores del tema
THEME_COLORS = {
    "primary": "#667eea",
    "secondary": "#764ba2",
    "success": "#28a745",
    "warning": "#ffc107",
    "danger": "#dc3545",
    "info": "#17a2b8",
    "dark": "#343a40",
    "light": "#f8f9fa"
}

# Archivos permitidos
ALLOWED_FILE_TYPES = ["xlsx"]

# Límites del sistema
SYSTEM_LIMITS = {
    "max_file_size_kb": 10240,  # 10MB
    "max_records_display": 1000,
    "session_timeout_minutes": 60
}
