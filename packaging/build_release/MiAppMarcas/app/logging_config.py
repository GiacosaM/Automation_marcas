"""
Configuración centralizada del logging para la aplicación Streamlit.

- Consola: solo WARNING y ERROR.
- Archivo logs/app.log: INFO, WARNING y ERROR (con rotación).

Debe llamarse setup_logging() al inicio de la app, antes de importar
módulos que usen logging (p. ej. database.py).
"""
import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    """
    Configura el root logger para toda la aplicación:
    - Consola (StreamHandler): solo WARNING y ERROR.
    - Archivo logs/app.log: INFO, WARNING y ERROR.
    """
    root = logging.getLogger()
    # Limpiar handlers existentes para evitar duplicados o configuración previa
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Directorio de logs junto al directorio de este archivo (raíz de la app)
    app_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(app_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    log_file = os.path.join(logs_dir, "app.log")

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Archivo: INFO y superior (rotación: 5 MB por archivo, 3 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Consola: solo WARNING y ERROR
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    root.setLevel(logging.DEBUG)
