# professional_theme.py
"""
Módulo de tema profesional para reportes PDF
Contiene configuraciones de colores, tipografías y estilos para un aspecto elegante
"""

class ProfessionalTheme:
    """Configuración de tema profesional para reportes PDF"""
    
    # Colores principales (RGB)
    COLORS = {
        'primary_blue': (41, 98, 255),      # Azul principal para títulos
        'secondary_blue': (72, 133, 237),   # Azul secundario
        'light_blue': (230, 242, 255),      # Azul claro para fondos
        'dark_gray': (45, 45, 45),          # Gris oscuro para texto principal
        'medium_gray': (80, 80, 80),        # Gris medio
        'light_gray': (240, 240, 240),      # Gris claro para separadores
        'white': (255, 255, 255),           # Blanco
        'black': (0, 0, 0),                 # Negro
        'table_header': (52, 73, 94),       # Color de cabecera de tabla
        'table_row_alt': (248, 249, 250),   # Color alternado de filas
        'border_color': (220, 220, 220),    # Color de bordes
        'confidential_text': (128, 128, 128) # Color texto confidencial
    }
    
    # Tipografías y tamaños
    FONTS = {
        'main_title': {'family': 'Arial', 'style': 'B', 'size': 20},
        'subtitle': {'family': 'Arial', 'style': 'B', 'size': 14},
        'section_title': {'family': 'Arial', 'style': 'B', 'size': 12},
        'header_company': {'family': 'Arial', 'style': 'B', 'size': 14},
        'header_info': {'family': 'Arial', 'style': '', 'size': 9},
        'table_header': {'family': 'Arial', 'style': 'B', 'size': 9},
        'table_content': {'family': 'Arial', 'style': '', 'size': 8},
        'normal_text': {'family': 'Arial', 'style': '', 'size': 10},
        'small_text': {'family': 'Arial', 'style': '', 'size': 8},
        'footer_text': {'family': 'Arial', 'style': 'I', 'size': 7}
    }
    
    # Márgenes y espaciados
    LAYOUT = {
        'margin_left': 25,
        'margin_right': 25,
        'margin_top': 30,
        'margin_bottom': 25,
        'header_height': 40,
        'footer_height': 20,
        'section_spacing': 15,
        'paragraph_spacing': 8,
        'line_height': 6,
        'table_row_height': 7,
        'watermark_size': 15  # Reducido al 15% del ancho de página
    }
    
    # Configuración de tablas
    TABLE = {
        'border_width': 0.3,
        'header_height': 8,
        'row_height': 6,
        'padding': 2,
        'zebra_stripe': True,
        'header_bold': True
    }
    
    @classmethod
    def get_color(cls, color_name: str) -> tuple:
        """Obtiene un color por nombre"""
        return cls.COLORS.get(color_name, cls.COLORS['black'])
    
    @classmethod
    def get_font(cls, font_name: str) -> dict:
        """Obtiene configuración de fuente por nombre"""
        return cls.FONTS.get(font_name, cls.FONTS['normal_text'])
    
    @classmethod
    def get_layout(cls, property_name: str) -> int:
        """Obtiene una propiedad de layout por nombre"""
        return cls.LAYOUT.get(property_name, 0)
