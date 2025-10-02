#!/usr/bin/env python3
"""
Ejemplo completo de configuración de logging con appdirs.
Este módulo proporciona funciones para configurar el logging de forma centralizada
usando appdirs para garantizar que los archivos se guarden en ubicaciones apropiadas
del sistema operativo.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import appdirs

# Configuración de la aplicación
APP_NAME = "MiAppMarcas"
APP_AUTHOR = "GiacosaM"
LOG_FILENAME = "app.log"
DEBUG_LOG_FILENAME = "debug.log"

def ensure_dir_exists(directory):
    """
    Asegura que un directorio exista, creándolo si es necesario.
    
    Args:
        directory (str): Ruta del directorio a verificar/crear.
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    return directory

def get_app_data_dir():
    """
    Obtiene el directorio de datos de la aplicación usando appdirs.
    
    Returns:
        str: Ruta al directorio de datos de la aplicación.
    """
    # Opción 1: Usar appdirs para obtener la ubicación estándar del sistema
    data_dir = appdirs.user_data_dir(APP_NAME, APP_AUTHOR)
    
    # Opción 2: Ubicación personalizada (ejemplo: en el escritorio)
    # data_dir = os.path.join(os.path.expanduser("~/Desktop"), APP_NAME)
    
    return ensure_dir_exists(data_dir)

def get_app_log_dir():
    """
    Obtiene el directorio para los logs de la aplicación.
    
    Returns:
        str: Ruta al directorio de logs.
    """
    log_dir = os.path.join(get_app_data_dir(), "logs")
    return ensure_dir_exists(log_dir)

def setup_logging(log_level=logging.INFO, console=True, file=True, 
                  log_file_name=None, max_file_size=5*1024*1024, backup_count=3):
    """
    Configura el sistema de logging con múltiples opciones.
    
    Args:
        log_level (int): Nivel de logging (default: logging.INFO)
        console (bool): Si True, muestra los logs en consola
        file (bool): Si True, guarda los logs en archivo
        log_file_name (str): Nombre del archivo de log (default: app.log)
        max_file_size (int): Tamaño máximo del archivo de log en bytes antes de rotar
        backup_count (int): Número de copias de respaldo a mantener
        
    Returns:
        str: Ruta completa al archivo de log principal (si file=True)
    """
    # Reset de la configuración previa (útil en caso de reconfiguración)
    logging.root.handlers = []
    
    # Configuración del formato de los logs
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Crear el logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    handlers = []
    
    # Handler para la consola
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)
    
    log_file_path = None
    # Handler para el archivo
    if file:
        if log_file_name is None:
            log_file_name = LOG_FILENAME
            
        log_dir = get_app_log_dir()
        log_file_path = os.path.join(log_dir, log_file_name)
        
        # Usar RotatingFileHandler para evitar archivos de log demasiado grandes
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Añadir todos los handlers al logger
    for handler in handlers:
        root_logger.addHandler(handler)
    
    # Log inicial para confirmar la configuración
    if log_file_path:
        logging.info(f"Logging configurado. Archivo de log: {log_file_path}")
    else:
        logging.info("Logging configurado sólo para consola.")
    
    return log_file_path

def setup_module_logger(module_name, log_level=None):
    """
    Configura un logger específico para un módulo.
    
    Args:
        module_name (str): Nombre del módulo
        log_level (int, optional): Nivel de logging específico para este módulo
        
    Returns:
        Logger: Logger configurado para el módulo
    """
    logger = logging.getLogger(module_name)
    if log_level is not None:
        logger.setLevel(log_level)
    return logger

# Ejemplo de uso
if __name__ == "__main__":
    # Configuración básica
    log_file = setup_logging(
        log_level=logging.DEBUG,
        console=True,
        file=True,
        log_file_name="ejemplo_logging.log"
    )
    
    # Uso del logger raíz
    logging.debug("Este es un mensaje de debug")
    logging.info("Este es un mensaje informativo")
    logging.warning("Este es un mensaje de advertencia")
    logging.error("Este es un mensaje de error")
    
    # Ejemplo de logger para un módulo específico
    module_logger = setup_module_logger("mi_modulo")
    module_logger.info("Log desde un módulo específico")
    
    # Mostrar ruta del archivo de log
    print(f"El archivo de log se encuentra en: {log_file}")
    
    # Directorio de datos de la aplicación
    print(f"Directorio de datos: {get_app_data_dir()}")
    print(f"Directorio de logs: {get_app_log_dir()}")