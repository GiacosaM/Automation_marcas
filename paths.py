#!/usr/bin/env python3
"""
Módulo para centralizar todas las rutas de la aplicación MiAppMarcas.

Este módulo proporciona funciones para obtener y gestionar rutas de archivos 
y directorios utilizados por la aplicación, asegurando consistencia en la 
localización de recursos a través de todo el proyecto.
"""

import os
import appdirs

# Nombre de la aplicación para la gestión de directorios
APP_NAME = "MiAppMarcas"
APP_AUTHOR = "GiacosaM"  # Nombre del autor o empresa

def get_data_dir():
    """
    Obtiene el directorio de datos de la aplicación.
    Crea el directorio si no existe.
    
    Returns:
        str: Ruta absoluta al directorio de datos.
    """
    # Usar una ubicación visible en el escritorio en lugar de la biblioteca oculta
    app_name = "MiAppMarcas"
    # data_dir = user_data_dir(app_name, appauthor=None)  # Comentado: ruta en la biblioteca
    data_dir = os.path.join(os.path.expanduser("~/Desktop"), app_name)  # Nueva ruta en el escritorio
    
    # Crear el directorio si no existe
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
    
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
    return os.path.join(get_data_dir(), "config.json")

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
    
def get_image_path(image_name=None):
    """
    Obtiene la ruta completa a un archivo de imagen o al directorio de imágenes.
    
    Args:
        image_name (str, optional): Nombre del archivo de imagen. Si es None,
                                   devuelve el directorio de imágenes.
    
    Returns:
        str: Ruta absoluta al archivo de imagen o al directorio de imágenes.
    """
    images_dir = os.path.join(get_project_root(), "imagenes")
    if image_name:
        return os.path.join(images_dir, image_name)
    return images_dir

# Si se ejecuta como script principal, mostrar información de las rutas
if __name__ == "__main__":
    print(f"Directorio de datos: {get_data_dir()}")
    print(f"Ruta de base de datos: {get_db_path()}")
    print(f"Directorio de informes: {get_informes_dir()}")
    print(f"Directorio de logs: {get_logs_dir()}")
    print(f"Directorio temporal: {get_temp_dir()}")
    print(f"Archivo de configuración: {get_config_file_path()}")
    print(f"Raíz del proyecto: {get_project_root()}")
    print(f"Directorio de imágenes: {get_image_path()}")
    print(f"Imagen de marca de agua: {get_image_path('marca_agua.jpg')}")