#!/usr/bin/env python3

import os
import sys
import logging

# Añadir el directorio padre al Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import crear_conexion

def crear_tabla_verificaciones_log():
    """Crea la tabla verificaciones_log si no existe."""
    conn = crear_conexion()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS verificaciones_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_ejecucion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            mes_ejecutado TEXT NOT NULL,  -- formato 'YYYY-MM'
            resultado TEXT CHECK(resultado IN ('exitosa', 'fallida', 'en_progreso')) NOT NULL,
            titulares_procesados INTEGER DEFAULT 0,
            error_mensaje TEXT
        )
        """)
        
        # Crear índice para búsquedas eficientes por mes_ejecutado
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_verificaciones_mes 
        ON verificaciones_log(mes_ejecutado)
        """)
        
        conn.commit()
        logging.info("Tabla verificaciones_log creada exitosamente")
        
    except Exception as e:
        logging.error(f"Error al crear tabla verificaciones_log: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    crear_tabla_verificaciones_log()