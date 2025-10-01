#!/usr/bin/env python3

"""
Script para inicializar la base de datos en la nueva ubicación.
"""

import os
from paths import get_db_path, get_data_dir, get_logs_dir, get_informes_dir
from database import crear_conexion, crear_tabla

# Asegurarse de que todos los directorios necesarios existan
print(f"Creando directorios de datos en: {get_data_dir()}")
os.makedirs(get_data_dir(), exist_ok=True)
os.makedirs(get_logs_dir(), exist_ok=True) 
os.makedirs(get_informes_dir(), exist_ok=True)

# Crear base de datos con la estructura inicial
print(f"Creando base de datos en: {get_db_path()}")
conn = crear_conexion()
crear_tabla(conn)
conn.close()

print("✅ Base de datos inicializada correctamente.")
print("✅ Directorios creados:")
print(f"  - Directorio de datos: {get_data_dir()}")
print(f"  - Directorio de logs: {get_logs_dir()}")  
print(f"  - Directorio de informes: {get_informes_dir()}")
print(f"  - Base de datos: {get_db_path()}")