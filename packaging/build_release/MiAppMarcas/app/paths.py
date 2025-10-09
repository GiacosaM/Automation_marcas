#!/usr/bin/env python3
"""
Módulo para centralizar todas las rutas de la aplicación MiAppMarcas.

Este módulo proporciona funciones para obtener y gestionar rutas de archivos 
y directorios utilizados por la aplicación, asegurando consistencia en la 
localización de recursos a través de todo el proyecto.
"""

import os
import sys
import appdirs

# Nombre de la aplicación para la gestión de directorios
APP_NAME = "MiAppMarcas"
APP_AUTHOR = "GiacosaM"  # Nombre del autor o empresa

def get_base_dir():
    """
    Detecta el directorio base de la aplicación.
    Si se está ejecutando desde un ejecutable empaquetado, usa el directorio del ejecutable.
    Si se está ejecutando como script Python, usa el directorio del script.
    
    Returns:
        str: Ruta absoluta al directorio base de la aplicación.
    """
    # Detectar si estamos en un ejecutable empaquetado con PyInstaller
    if getattr(sys, 'frozen', False):
        # Ejecutable empaquetado: usar el directorio padre del ejecutable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Script Python: usar el directorio del script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    return base_dir

def get_data_dir():
    """
    Obtiene el directorio de datos de la aplicación.
    Crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio de datos.
    """
    # Si estamos ejecutando localmente y queremos usar una ubicación específica
    if os.path.exists("/Users/martingiacosa/Desktop/MiAppMarcas"):
        data_dir = "/Users/martingiacosa/Desktop/MiAppMarcas"
    else:
        # Usar el directorio base de la aplicación (donde está el ejecutable o el script)
        data_dir = get_base_dir()
    
    # Crear subdirectorios necesarios
    for subdir in ['assets', 'imagenes', 'informes', 'logs', 'config']:
        full_path = os.path.join(data_dir, subdir)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
    
    return data_dir

def get_db_path():
    """
    Obtiene la ruta completa del archivo de base de datos SQLite.
    
    Returns:
        str: Ruta absoluta al archivo de base de datos "boletines.db".
    """
    return os.path.join(get_data_dir(), "boletines.db")

def get_informes_dir():
    """
    Obtiene la ruta del directorio para almacenar informes generados.
    
    La función crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio de informes.
    """
    informes_dir = os.path.join(get_data_dir(), "informes")
    
    # Crear el directorio si no existe
    if not os.path.exists(informes_dir):
        os.makedirs(informes_dir, exist_ok=True)
    
    return informes_dir

def get_logs_dir():
    """
    Obtiene la ruta del directorio para almacenar archivos de log.
    
    La función crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio de logs.
    """
    logs_dir = os.path.join(get_data_dir(), "logs")
    
    # Crear el directorio si no existe
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    
    return logs_dir

def get_temp_dir():
    """
    Obtiene la ruta del directorio temporal para la aplicación.
    
    La función crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio temporal.
    """
    temp_dir = os.path.join(get_data_dir(), "temp")
    
    # Crear el directorio si no existe
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    
    return temp_dir

def get_config_file_path():
    """
    Obtiene la ruta completa del archivo de configuración.
    
    Returns:
        str: Ruta absoluta al archivo "config.json".
    """
    # Buscar primero en el directorio principal de la aplicación
    config_path = os.path.join(get_data_dir(), "config.json")
    
    # Si no existe, buscar en el subdirectorio config
    if not os.path.exists(config_path):
        config_subdir = os.path.join(get_data_dir(), "config", "config.json")
        if os.path.exists(config_subdir):
            return config_subdir
    
    return config_path

# Función de utilidad para obtener rutas relativas al directorio del proyecto
def get_project_root():
    """
    Obtiene la ruta raíz del proyecto (directorio donde se ejecuta el script).
    
    Returns:
        str: Ruta absoluta al directorio raíz del proyecto.
    """
    # Por defecto, consideramos que la raíz del proyecto es donde se encuentra este archivo
    return os.path.dirname(os.path.abspath(__file__))

def get_project_file(relative_path):
    """
    Construye una ruta a un archivo relativo a la raíz del proyecto.
    
    Args:
        relative_path (str): Ruta relativa desde la raíz del proyecto.
        
    Returns:
        str: Ruta absoluta al archivo dentro del proyecto.
    """
    return os.path.join(get_project_root(), relative_path)
    
def get_assets_dir():
    """
    Obtiene la ruta del directorio de assets de la aplicación.
    Crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio de assets.
    """
    assets_dir = os.path.join(get_data_dir(), "assets")
    
    # Crear el directorio si no existe
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir, exist_ok=True)
    
    return assets_dir

def get_image_path(image_name=None):
    """
    Obtiene la ruta completa a un archivo de imagen o al directorio de imágenes.
    
    Args:
        image_name (str, optional): Nombre del archivo de imagen. Si es None,
                                   devuelve el directorio de imágenes.
    
    Returns:
        str: Ruta absoluta al archivo de imagen o al directorio de imágenes.
    """
    # Primero intentar en el directorio de datos de la aplicación
    images_dir = os.path.join(get_data_dir(), "imagenes")
    
    # Si no existe, intentar en el directorio del proyecto (modo desarrollo)
    if not os.path.exists(images_dir):
        images_dir = os.path.join(get_project_root(), "imagenes")
    
    if image_name:
        return os.path.join(images_dir, image_name)
    return images_dir

def inicializar_assets():
    """
    Inicializa los assets de la aplicación (logo, imágenes, etc.)
    copiándolos desde el directorio del proyecto al directorio de assets del usuario.
    
    Returns:
        bool: True si la inicialización fue exitosa, False en caso contrario.
    """
    import shutil
    
    # Asegurarnos de que el directorio de assets exista
    assets_dir = get_assets_dir()
    
    # Lista de archivos a copiar desde el directorio de imágenes
    assets_to_copy = {
        'marca_agua.jpg': 'logo.jpg',  # Renombrar marca_agua.jpg a logo.jpg
        'image1.jpg': 'logo_alt.jpg'   # Alternativo por si marca_agua.jpg no existe
    }
    
    success = False
    
    # Copiar cada archivo de imagen al directorio de assets
    for src_name, dest_name in assets_to_copy.items():
        src_path = get_image_path(src_name)
        dest_path = os.path.join(assets_dir, dest_name)
        
        # Verificar si el archivo de origen existe
        if os.path.exists(src_path) and not os.path.exists(dest_path):
            try:
                shutil.copy2(src_path, dest_path)
                print(f"Asset copiado: {src_path} → {dest_path}")
                success = True
                # Si se copió correctamente uno, no es necesario copiar alternativas
                if dest_name == 'logo.jpg':
                    break
            except Exception as e:
                print(f"Error al copiar asset {src_name}: {e}")
                
    return success

def get_logo_path():
    """
    Obtiene la ruta al logo de la aplicación.
    Si no existe en el directorio de assets, intenta inicializarlo.
    
    Returns:
        str: Ruta absoluta al archivo de logo o None si no se encuentra.
    """
    logo_path = os.path.join(get_assets_dir(), "logo.jpg")
    alt_logo_path = os.path.join(get_assets_dir(), "logo_alt.jpg")
    
    # Verificar si el logo principal existe
    if os.path.exists(logo_path):
        return logo_path
    
    # Verificar si el logo alternativo existe
    if os.path.exists(alt_logo_path):
        return alt_logo_path
    
    # Si no existe ninguno, intentar inicializar los assets
    if inicializar_assets():
        return get_logo_path()  # Llamada recursiva después de inicializar
    
    # Si no se pudo obtener el logo de ninguna forma, intentar retornar
    # la ruta directa a la imagen en el directorio del proyecto
    project_logo = get_image_path("marca_agua.jpg")
    if os.path.exists(project_logo):
        return project_logo
        
    return None

# Si se ejecuta como script principal, mostrar información de las rutas
if __name__ == "__main__":
    print(f"Directorio de datos: {get_data_dir()}")
    print(f"Ruta de base de datos: {get_db_path()}")
    print(f"Directorio de informes: {get_informes_dir()}")
    print(f"Directorio de logs: {get_logs_dir()}")
    print(f"Directorio temporal: {get_temp_dir()}")
    print(f"Directorio de assets: {get_assets_dir()}")
    print(f"Archivo de configuración: {get_config_file_path()}")
    print(f"Raíz del proyecto: {get_project_root()}")
    print(f"Directorio de imágenes: {get_image_path()}")
    print(f"Logo de la aplicación: {get_logo_path()}")