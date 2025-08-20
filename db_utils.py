"""
Utilidades para operaciones de base de datos
Este módulo contiene funciones auxiliares para trabajar con bases de datos
que no tienen dependencias circulares con otros módulos
"""
import os
import json

def usar_supabase_simple():
    """
    Implementación simplificada de usar_supabase que solo usa variables de entorno
    o archivo de configuración sin dependencias circulares
    """
    # Primero intentamos leer variables de entorno
    if os.getenv('SUPABASE_URL'):
        return True
    
    # Si no hay variables de entorno, intentamos leer el archivo config.json
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                config = json.load(f)
                if 'database' in config and 'type' in config['database']:
                    return config['database']['type'].lower() == 'supabase'
    except:
        pass
        
    # Por defecto, asumimos SQLite si no hay configuración
    return False

def convertir_query_boolean(query):
    """
    Convierte queries de SQLite a PostgreSQL de forma simple y confiable
    - Solo maneja booleanos: = 0/1 a = FALSE/TRUE  
    - Para queries complejas de fechas, se usarán versiones específicas de PostgreSQL
    """
    if not usar_supabase_simple():
        return query  # Si no es Supabase, devolver sin cambios
    
    # Convertir comparaciones booleanas simples
    query = query.replace("reporte_generado = 1", "reporte_generado = TRUE")
    query = query.replace("reporte_generado = 0", "reporte_generado = FALSE")
    query = query.replace("reporte_enviado = 1", "reporte_enviado = TRUE")
    query = query.replace("reporte_enviado = 0", "reporte_enviado = FALSE")
    query = query.replace("is_active = 1", "is_active = TRUE")
    query = query.replace("is_active = 0", "is_active = FALSE")
    
    return query
    query = query.replace("is_active = 1", "is_active = TRUE")
    query = query.replace("is_active = 0", "is_active = FALSE")
    
    return query
