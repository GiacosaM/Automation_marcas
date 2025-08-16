"""
Script para actualizar la estructura de la base de datos
y agregar una columna para el periodo de notificación
"""
import sqlite3
import logging
from datetime import datetime

# Configuración básica de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def actualizar_base_datos():
    """
    Actualiza la estructura de la tabla emails_enviados para añadir
    una columna que almacene el periodo de notificación.
    """
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('boletines.db')
        cursor = conn.cursor()
        
        # Verificar si la columna ya existe
        cursor.execute("PRAGMA table_info(emails_enviados)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'periodo_notificacion' not in columnas:
            logging.info("Agregando columna periodo_notificacion a la tabla emails_enviados")
            cursor.execute("""
                ALTER TABLE emails_enviados 
                ADD COLUMN periodo_notificacion TEXT DEFAULT NULL
            """)
            conn.commit()
            logging.info("Columna agregada correctamente")
        else:
            logging.info("La columna periodo_notificacion ya existe")
            
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error al actualizar la estructura de la base de datos: {e}")
        return False

if __name__ == "__main__":
    print("Actualizando estructura de la base de datos...")
    if actualizar_base_datos():
        print("✅ Actualización completada correctamente")
    else:
        print("❌ Error al actualizar la base de datos")
